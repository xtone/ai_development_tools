# DmenuNewsプロジェクト Data Layer 実装ガイド

## 概要

このドキュメントは、DmenuNewsプロジェクトにおけるdata layer実装パターンを詳細に解説します。

---

## 1. Room Database

### 1.1 Database定義

**ファイル**: `data/src/main/kotlin/.../data/common/room/AppDatabase.kt`

```kotlin
@Database(
    entities = [
        UserTab::class, ProcessedTab::class, SearchNewsHistory::class,
        AlreadyReadNews::class, PushDataId::class, KeywordRecommend::class,
        FavoriteArticle::class, BrowsingHistory::class,
    ],
    version = 6,
    exportSchema = false,
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userTabDao(): UserTabDao
    abstract fun processedTabDao(): ProcessedTabDao
    abstract fun searchWord(): SearchNewsHistoryDao
    abstract fun alreadyReadNewsDao(): AlreadyReadNewsDao
    abstract fun pushDataIdDao(): PushDataIdDao
    abstract fun keywordRecommendDao(): KeywordRecommendDao
    abstract fun favoriteArticleDao(): FavoriteArticleDao
    abstract fun browsingHistoryDao(): BrowsingHistoryDao
}
```

**設計判断**:
- `exportSchema = false`: スキーマ検証なし（CI/CD でのテスト効率化）
- Factory パターンで DI実装（テスト時のモック化を容易に）
- 8つのEntity で機能ごとにテーブルを分離

### 1.2 Entity 定義パターン

#### パターン1: 単一主キー + 複数カラム

**ファイル**: `data/.../room/model/FavoriteArticle.kt`

```kotlin
@Entity(tableName = "favorite_articles")
data class FavoriteArticle(
    @PrimaryKey
    val articleId: String,
    @ColumnInfo(name = "saved_at")
    val savedAt: Long,
    @ColumnInfo(name = "article_title")
    val articleTitle: String,
    @ColumnInfo(name = "article_url")
    val articleUrl: String,
    @ColumnInfo(name = "thumbnail_url")
    val thumbnailUrl: String?,
    @ColumnInfo(name = "published_date")
    val publishedDate: Long,
    @ColumnInfo(name = "video_duration")
    val videoDuration: String? = null,
)
```

**ポイント**:
- `@ColumnInfo(name = "snake_case")`: DBカラム名はsnake_case
- `String?` / `= null`: nullable フィールドの明示
- `Long` で日時を管理（Unix timestamp）

#### パターン2: 複合主キー

**ファイル**: `data/.../room/model/AlreadyReadNews.kt`

```kotlin
@Entity(primaryKeys = ["categoryId", "articleId"])
data class AlreadyReadNews(
    val categoryId: String,
    val articleId: String,
)
```

**ポイント**:
- `primaryKeys = [...]` で複合主キー定義
- カテゴリ×記事の組み合わせでユニーク

#### パターン3: シンプルEntity

**ファイル**: `data/.../room/model/KeywordRecommend.kt`

```kotlin
@Entity("keyword_recommend")
data class KeywordRecommend(
    @PrimaryKey
    @ColumnInfo("id")
    val id: String,
    @ColumnInfo("title")
    val title: String,
    @ColumnInfo("count")
    val count: Int,
    @ColumnInfo("created_at")
    val createdAt: Long,
)
```

### 1.3 DAO 設計パターン

#### パターン1: Flow返却 + suspend関数混在

**ファイル**: `data/.../room/dao/FavoriteArticleDao.kt`

```kotlin
@Dao
abstract class FavoriteArticleDao(
    override val database: RoomDatabase,
) : Transactionable {
    // リアルタイム監視用 (Flow)
    @Query("SELECT * FROM favorite_articles ORDER BY saved_at DESC")
    abstract fun streamFavorites(): Flow<List<FavoriteArticle>>

    // 単発取得 (suspend)
    @Query("SELECT * FROM favorite_articles ORDER BY saved_at DESC LIMIT :limit")
    abstract suspend fun getFavorites(limit: Int): List<FavoriteArticle>

    // 存在チェック
    @Query("SELECT EXISTS(SELECT 1 FROM favorite_articles WHERE articleId = :articleId)")
    abstract suspend fun exists(articleId: String): Boolean

    // CRUD操作
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    abstract suspend fun insert(article: FavoriteArticle)

    @Delete
    abstract suspend fun delete(article: FavoriteArticle)

    @Query("DELETE FROM favorite_articles WHERE articleId = :articleId")
    abstract suspend fun deleteById(articleId: String)

    // 古いデータの削除
    @Query("DELETE FROM favorite_articles WHERE saved_at < :threshold")
    abstract suspend fun deleteOldArticles(threshold: Long)
}
```

**設計判断**:
- `Flow<List<T>>`: UIでリアルタイム更新が必要な場合
- `suspend fun`: 単発の非同期操作
- `OnConflictStrategy.REPLACE`: Upsert パターン
- `EXISTS`: 存在チェックの効率化

#### パターン2: Transaction サポート

**ファイル**: `data/.../room/dao/KeywordRecommendDao.kt`

```kotlin
@Dao
interface KeywordRecommendDao {
    @Query("""
        SELECT * FROM keyword_recommend
        WHERE count >= 3
        ORDER BY count DESC, created_at ASC
    """)
    suspend fun getCount3OrMoteKeywordRecommends(): List<KeywordRecommend>

    // 同一idがあればcount+1でupdate、なければ1でinsert
    @Transaction
    suspend fun incrementKeywordRecommendCount(keywords: List<Keyword>) {
        keywords.forEach { keyword ->
            val record = getKeywordRecommendById(keyword.id.id)
            val keywordRecommend =
                record?.copy(count = record.count + 1)
                    ?: KeywordRecommend(
                        id = keyword.id.id,
                        title = keyword.title,
                        count = 1,
                        createdAt = System.currentTimeMillis(),
                    )
            upsertKeywordRecommend(keywordRecommend)
        }
    }

    @Query("SELECT * FROM keyword_recommend WHERE id = :id LIMIT 1")
    suspend fun getKeywordRecommendById(id: String): KeywordRecommend?

    @Upsert
    suspend fun upsertKeywordRecommend(keyword: KeywordRecommend)
}
```

**ポイント**:
- `@Transaction`: 複数操作の一貫性保証
- `@Upsert`: Insert or Update を1つのアノテーションで

#### パターン3: キープ数制限付き削除

**ファイル**: `data/.../room/dao/SearchNewsHistoryDao.kt`

```kotlin
@Dao
interface SearchNewsHistoryDao {
    @Query("SELECT * FROM search_news_history ORDER BY updated_at DESC")
    fun getAll(): Flow<List<SearchNewsHistory>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun save(history: SearchNewsHistory)

    @Query("DELETE FROM search_news_history WHERE word = :word")
    suspend fun deleteByWord(word: String)

    // 最新N件以外を削除
    @Query("""
        DELETE FROM search_news_history
        WHERE word NOT IN (
            SELECT word FROM search_news_history
            ORDER BY updated_at DESC
            LIMIT :keepCnt
        )
    """)
    suspend fun deleteOld(keepCnt: Int)
}
```

### 1.4 Transactionable インターフェース

**ファイル**: `data/.../room/dao/Transactionable.kt`

```kotlin
interface Transactionable {
    companion object {
        suspend inline fun <R, T : Transactionable> T.withTransaction(
            crossinline block: suspend T.() -> R
        ): R = database.withTransaction {
            block(this)
        }
    }
    val database: RoomDatabase
}
```

**用途**: DAO で複数の操作をトランザクション内で実行

### 1.5 Migration 実装

**ファイル**: `data/.../migration/DatabaseMigrations.kt`

```kotlin
val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(database: SupportSQLiteDatabase) {
        val insertSql = """
            INSERT OR IGNORE INTO UserTab (id, name, isDeletable, isSortable, `order`, visited, showAddNoticeBanner)
            VALUES (?, ?, ?, ?, (SELECT IFNULL(MAX(`order`), 0) + 1 FROM UserTab), ?, ?)
        """.trimIndent()

        try {
            database.execSQL(insertSql, arrayOf(
                "follow", "フォロー", 1, 1, 0, 1
            ))
            Timber.d("Migration 3->4: Successfully inserted follow tab.")
        } catch (e: Exception) {
            Timber.e(e, "Migration 3->4: Failed to insert follow tab.")
            throw e
        }
    }
}

val MIGRATION_4_5 = object : Migration(4, 5) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("""
            CREATE TABLE IF NOT EXISTS keyword_recommend (
                id TEXT PRIMARY KEY NOT NULL,
                title TEXT NOT NULL,
                count INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            )
        """.trimIndent())
    }
}
```

**ポイント**:
- `INSERT OR IGNORE`: 既存データがあれば無視
- `CREATE TABLE IF NOT EXISTS`: 冪等性の確保
- `try-catch` + `Timber`: エラー時のログ出力

---

## 2. DataStore

### 2.1 Preferences DataStore セットアップ

**ファイル**: `data/.../datastore/DataStoreProvider.kt`

```kotlin
class DataStoreProviderImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    roomMigration: RoomMigration,
) : DataStoreProvider {
    private val dataSource = PreferenceDataStoreFactory.create(
        produceFile = {
            context.preferencesDataStoreFile("settings")
        },
        migrations = listOf(
            roomMigration,
            SharedPreferencesMigration(
                context = context,
                sharedPreferencesName = context.packageName + "_preferences",
                keysToMigrate = LegacyAppPreferenceKey.entries
                    .asSequence()
                    .filterNot { it in skipKeys }
                    .map { it.value }
                    .toSet(),
            ),
        ),
        corruptionHandler = ReplaceFileCorruptionHandler { emptyPreferences() },
    )

    override fun provide(): DataStore<Preferences> = dataSource
}
```

**設計判断**:
- SharedPreferences からの段階的マイグレーション対応
- ファイル破損時は空のPreferencesで初期化

### 2.2 DataStore キー定義（型安全）

**ファイル**: `data/.../migration/DataStoreKey.kt`

```kotlin
sealed class DataStoreKey<T>(
    val key: Preferences.Key<T>,
    val defaultValue: T,
) {
    data object TosVersion : DataStoreKey<Int>(
        key = intPreferencesKey(LegacyAppPreferenceKey.TOS_VERSION.value),
        defaultValue = 0,
    )

    data object ArticleFontSize : DataStoreKey<Int>(
        key = intPreferencesKey(LegacyAppPreferenceKey.ARTICLE_FONT_SIZE.value),
        defaultValue = 16, // NORMAL
    )

    data object WeatherPrefectureCode : DataStoreKey<String>(
        key = stringPreferencesKey(LegacyAppPreferenceKey.WEATHER_PREFECTURE_CODE.value),
        defaultValue = "13", // 東京
    )

    data object ReadOptionalAddTabDialogs : DataStoreKey<Set<String>>(
        key = stringSetPreferencesKey(LegacyAppPreferenceKey.READ_OPTIONAL_ADD_TAB_DIALOGS.value),
        defaultValue = emptySet(),
    )
    // ... 60+ 以上のキー定義
}
```

**メリット**:
- Sealed class で型安全なキー管理
- デフォルト値を明示的に定義
- IDE補完で間違いを防止

### 2.3 DataStore Repository 実装

**例1: マイリスト設定**

**ファイル**: `data/.../mylist/repository/MyListDataStoreRepositoryImpl.kt`

```kotlin
class MyListDataStoreRepositoryImpl @Inject constructor(
    private val dataStore: DataStore<Preferences>,
) : MyListDataStoreRepository {
    companion object {
        private val KEY_INTRO_DIALOG_SHOWN = booleanPreferencesKey("mylist_intro_dialog_shown")
        private val KEY_FAVORITE_SORT_ORDER = stringPreferencesKey("mylist_favorite_sort_order")
    }

    // 読み取り (Flow)
    override fun isIntroDialogShown(): Flow<Boolean> =
        dataStore.data.map { preferences ->
            preferences[KEY_INTRO_DIALOG_SHOWN] ?: false
        }

    // 書き込み (suspend)
    override suspend fun setIntroDialogShown(shown: Boolean) {
        dataStore.edit { preferences ->
            preferences[KEY_INTRO_DIALOG_SHOWN] = shown
        }
    }

    // Enum のシリアライズ
    override fun getFavoriteArticlesSortOrder(): Flow<SortOrder> =
        dataStore.data.map { preferences ->
            val orderString = preferences[KEY_FAVORITE_SORT_ORDER]
            when (orderString) {
                SortOrder.OLDEST_FIRST.name -> SortOrder.OLDEST_FIRST
                else -> SortOrder.NEWEST_FIRST
            }
        }
}
```

**例2: カウンターの管理**

**ファイル**: `data/.../tutorial/repository/TutorialLaunchCountRepositoryImpl.kt`

```kotlin
class TutorialLaunchCountRepositoryImpl @Inject constructor(
    dataStoreProvider: DataStoreProvider,
) : TutorialLaunchCountRepository {
    private val dataStore = dataStoreProvider.provide()

    override fun getTutorialLaunchCount(): Flow<Int> =
        dataStore.data.map {
            it[DataStoreKey.TutorialLaunchCount.key]
                ?: DataStoreKey.TutorialLaunchCount.defaultValue
        }

    override suspend fun incrementTutorialLaunchCount() {
        dataStore.edit { preferences ->
            val currentCount = preferences[DataStoreKey.TutorialLaunchCount.key]
                ?: DataStoreKey.TutorialLaunchCount.defaultValue
            preferences[DataStoreKey.TutorialLaunchCount.key] = currentCount + 1
        }
    }
}
```

---

## 3. Repository層

### 3.1 データソース統合パターン

**ファイル**: `data/.../mylist/repository/MyListRepositoryImpl.kt`

```kotlin
class MyListRepositoryImpl @Inject constructor(
    private val favoriteArticleDao: FavoriteArticleDao,
    private val browsingHistoryDao: BrowsingHistoryDao,
    private val myListDataStoreRepository: MyListDataStoreRepository,
) : MyListRepository {

    // Room + Flow: リアルタイム監視
    override fun streamFavoriteArticles(): Flow<List<FavoriteArticle>> =
        favoriteArticleDao.streamFavorites().map { list ->
            list.map { entity -> entity.toDomainModel() }
        }

    // Room + Result: エラーハンドリング付き取得
    override suspend fun getAllFavoriteArticles(): Result<List<FavoriteArticle>> =
        runCatching {
            favoriteArticleDao.getAllFavorites().map { it.toDomainModel() }
        }

    // Room + Result: 書き込み操作
    override suspend fun addFavoriteArticle(article: FavoriteArticle): Result<Unit> =
        runCatching {
            favoriteArticleDao.insert(article.toEntity())
        }

    // DataStore 統合
    override suspend fun isArticleDetailFavoriteTooltipShown(): Boolean =
        myListDataStoreRepository.isArticleDetailFavoriteTooltipShown()
}
```

**設計判断**:
- `Flow<T>`: UIでリアルタイム更新が必要なデータ
- `Result<T>`: エラー情報を保持したい操作
- `runCatching`: 例外を Result でラップ

### 3.2 Facade パターン

**ファイル**: `data/.../mylist/repository/FavoriteRepositoryImpl.kt`

```kotlin
class FavoriteRepositoryImpl @Inject constructor(
    private val myListRepository: MyListRepository,
) : FavoriteRepository {

    override fun streamFavorites(): Flow<List<MyListItem>> =
        myListRepository.streamFavoriteArticles().map { favorites ->
            favorites.map { it.toMyListItem() }
        }

    override suspend fun isFavorite(articleId: String): Boolean =
        myListRepository.isFavorite(articleId).getOrElse { false }

    // トランザクション的な操作
    override suspend fun toggleFavorite(item: MyListItem): Result<Boolean> =
        runCatching {
            if (isFavorite(item.articleId)) {
                removeFavorite(item.articleId).getOrThrow()
                false
            } else {
                addFavorite(item).getOrThrow()
                true
            }
        }
}
```

### 3.3 API + Paging 統合

**ファイル**: `data/.../freeword/repository/KeywordRepositoryImpl.kt`

```kotlin
class KeywordRepositoryImpl @Inject constructor(
    private val freewordApiService: FreewordApiService,
    private val mapper: FreewordKeywordToKeywordMapper,
) : KeywordRepository {

    // Paging ライブラリ統合
    override fun searchKeywords(
        keyword: String,
        searchType: FreewordSearchType,
    ): Pager<Int, Keyword> = Pager(
        config = PagingConfig(
            pageSize = 10,
            prefetchDistance = 10,
            enablePlaceholders = false,
        ),
        pagingSourceFactory = {
            SearchKeywordsPagingSource(
                freewordApiService = freewordApiService,
                mapper = mapper,
                keywordQuery = keyword,
                searchType = searchType,
            )
        },
    )

    // API呼び出し + Result
    override suspend fun getPickupKeywords(): Result<List<PickupKeyword>> =
        runCatching {
            val response = freewordApiService.get(
                keyword = "",
                page = 1,
                searchType = FreewordSearchType.ALL.ordinal,
            )
            response.pickups.map { it.toDomainModel() }
        }
}
```

### 3.4 エラーハンドリングパターン

```kotlin
// パターン1: Result + getOrElse
override suspend fun isFavorite(articleId: String): Boolean =
    myListRepository.isFavorite(articleId).getOrElse { false }

// パターン2: Result + getOrThrow (例外を伝播)
override suspend fun toggleFavorite(item: MyListItem): Result<Boolean> =
    runCatching {
        removeFavorite(item.articleId).getOrThrow()
        false
    }

// パターン3: Flow + catch
override fun streamData(): Flow<Data> =
    dataSource.stream()
        .catch { e -> emit(Data.empty()) }
        .map { it.toDomainModel() }
```

---

## 4. API/Network層

### 4.1 Retrofit ApiService

**ファイル**: `data/.../freeword/datasource/FreewordApiService.kt`

```kotlin
interface FreewordApiService {
    @GET("dmenu/${ApiConstants.API_VERSION}/freeword")
    @Headers("Content-type: application/json")
    suspend fun get(
        @Query("keyword") keyword: String,
        @Query("page") page: Int,
        @Query("search_type") searchType: Int,
    ): FreewordResponse
}
```

**ファイル**: `data/.../timeline/datasource/TimelineApiService.kt`

```kotlin
interface TimelineApiService {
    @GET("dmenu/${ApiConstants.API_VERSION}/articles/{category_id}")
    suspend fun get(
        @Path("category_id") categoryId: String? = null,
        @Query("page") page: Int,
        @Query("app_version") appVersion: String,
        @Query("os_version") osVersion: String,
        @Query("os") os: String = "android",
        @Query("cookie_id") cookieId: String,
        @Query("follow_ids[]", encoded = true) followIds: List<String>? = null,
        @Header("LA-Cookie") laCookie: String? = null,
    ): GetTimelineResponse
}
```

### 4.2 レスポンスモデル (kotlinx.serialization)

```kotlin
@Serializable
data class FreewordResponse(
    @SerialName("header")
    val header: HeaderResponse,
    @SerialName("pickups")
    var pickups: List<Pickup>,
    @SerialName("rows")
    val rows: List<MatchedKeyword>,
    @SerialName("page")
    val page: PageResponse,
) {
    @Serializable
    data class Pickup(
        @SerialName("data")
        val data: List<KeywordResponse>,
        @SerialName("layout")
        val layout: String? = null,
    )
}
```

---

## 5. よくあるミス・注意点

### 5.1 メインスレッドでのDB操作

```kotlin
// ❌ NG: メインスレッドでの同期呼び出し
fun getBadData(): List<Data> = dao.getAll()  // ブロッキング

// ✅ OK: suspend関数でIO Dispatcherを使用
suspend fun getGoodData(): List<Data> = withContext(Dispatchers.IO) {
    dao.getAll()
}

// ✅ OK: Flow で非同期監視
fun streamData(): Flow<List<Data>> = dao.streamAll()
```

### 5.2 Migration漏れ

```kotlin
// ❌ NG: バージョンを上げたがMigrationを定義していない
@Database(entities = [NewEntity::class], version = 7)
// → クラッシュ: IllegalStateException

// ✅ OK: Migrationを定義
val MIGRATION_6_7 = object : Migration(6, 7) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("CREATE TABLE IF NOT EXISTS ...")
    }
}

// Database作成時に登録
Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
    .addMigrations(MIGRATION_6_7)
    .build()
```

### 5.3 キャッシュ戦略の不備

```kotlin
// ❌ NG: 常にAPIを呼ぶ
override suspend fun getData(): Data = api.fetch()

// ✅ OK: キャッシュファースト
override suspend fun getData(): Data {
    val cached = dao.get()
    if (cached != null && !cached.isExpired()) {
        return cached.toDomainModel()
    }
    val fresh = api.fetch()
    dao.insert(fresh.toEntity())
    return fresh.toDomainModel()
}
```

### 5.4 メモリリーク

```kotlin
// ❌ NG: Flowをcollectし続ける（Activity/Fragmentで）
lifecycleScope.launch {
    repository.streamData().collect { /* 永遠にcollect */ }
}

// ✅ OK: lifecycle-awareなcollect
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        repository.streamData().collect { /* STARTED時のみ */ }
    }
}

// ✅ OK: ViewModelでstateIn
val data = repository.streamData()
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
```

---

## 6. テストパターン

### 6.1 Repository Unit Test

**ファイル**: `data/src/test/.../MyListRepositoryImplTest.kt`

```kotlin
class MyListRepositoryImplTest {
    private lateinit var favoriteArticleDao: FavoriteArticleDao
    private lateinit var repository: MyListRepositoryImpl

    @Before
    fun setup() {
        favoriteArticleDao = mockk(relaxed = true)
        repository = MyListRepositoryImpl(favoriteArticleDao, mockk(), mockk())
    }

    @Test
    fun `streamFavoriteArticles should return mapped domain models`() = runTest {
        val entities = listOf(createMockEntity("1", "Title 1"))
        every { favoriteArticleDao.streamFavorites() } returns flowOf(entities)

        val result = repository.streamFavoriteArticles().first()

        assertEquals(1, result.size)
        assertEquals("1", result[0].articleId)
        verify { favoriteArticleDao.streamFavorites() }
    }

    @Test
    fun `addFavoriteArticle should call dao insert`() = runTest {
        val article = createDomainModel("1", "Title")

        val result = repository.addFavoriteArticle(article)

        assertTrue(result.isSuccess)
        coVerify { favoriteArticleDao.insert(match { it.articleId == "1" }) }
    }
}
```

### 6.2 DataStore Repository Test

```kotlin
class MyListDataStoreRepositoryImplTest {
    private lateinit var dataStore: DataStore<Preferences>
    private lateinit var repository: MyListDataStoreRepositoryImpl

    @Before
    fun setup() {
        dataStore = mockk(relaxed = true)
        repository = MyListDataStoreRepositoryImpl(dataStore)
    }

    @Test
    fun `isIntroDialogShown should return false by default`() = runTest {
        val preferences = mutablePreferencesOf()
        every { dataStore.data } returns flowOf(preferences)

        val result = repository.isIntroDialogShown().first()

        assertFalse(result)
    }

    @Test
    fun `isIntroDialogShown should return true when set`() = runTest {
        val preferences = mutablePreferencesOf(
            booleanPreferencesKey("mylist_intro_dialog_shown") to true,
        )
        every { dataStore.data } returns flowOf(preferences)

        val result = repository.isIntroDialogShown().first()

        assertTrue(result)
    }
}
```

### 6.3 Room In-Memory Database Test

```kotlin
@RunWith(AndroidJUnit4::class)
class FavoriteArticleDaoTest {
    private lateinit var database: AppDatabase
    private lateinit var dao: FavoriteArticleDao

    @Before
    fun setup() {
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        dao = database.favoriteArticleDao()
    }

    @After
    fun teardown() {
        database.close()
    }

    @Test
    fun insertAndRetrieve() = runTest {
        val article = FavoriteArticle(
            articleId = "1",
            savedAt = 1000L,
            articleTitle = "Test",
            articleUrl = "url",
            thumbnailUrl = null,
            publishedDate = 1704067200L,
        )

        dao.insert(article)
        val result = dao.getAllFavorites()

        assertThat(result).hasSize(1)
        assertThat(result[0].articleId).isEqualTo("1")
    }
}
```

---

## 7. DI Module 設定

**ファイル**: `data/.../room/di/DatabaseModule.kt`

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Singleton
    @Provides
    fun provideDatabaseFactory(impl: AppDatabaseFactoryImpl): AppDatabaseFactory = impl

    @Singleton
    @Provides
    fun provideDatabase(factory: AppDatabaseFactory) = factory.create()

    @Singleton
    @Provides
    fun provideFavoriteArticleDao(database: AppDatabase) = database.favoriteArticleDao()

    @Singleton
    @Provides
    fun provideBrowsingHistoryDao(database: AppDatabase) = database.browsingHistoryDao()
}
```

---

## 8. アーキテクチャまとめ

### レイヤー構成

```
Presentation Layer (UI/ViewModel)
        ↓
Domain Layer (UseCase/Repository Interface)
        ↓
Data Layer (Repository Implementation)
        ├── Room (ローカルDB)
        ├── DataStore (Preferences)
        ├── API (Retrofit)
        └── Mapper (Model変換)
```

### データフローパターン

| パターン | 用途 | 実装 |
|----------|------|------|
| Flow | リアルタイム更新 | `dao.stream()` → `Flow<List<T>>` |
| suspend + Result | 単発操作 | `runCatching { dao.get() }` |
| Paging | 大量データ | `Pager + PagingSource` |

### エラーハンドリング

| 方式 | 用途 |
|------|------|
| `Result<T>` | 成功/失敗を明確に |
| `runCatching{}` | 例外をResultでラップ |
| `.getOrElse { default }` | デフォルト値でフォールバック |
| `.getOrThrow()` | 例外を伝播 |
