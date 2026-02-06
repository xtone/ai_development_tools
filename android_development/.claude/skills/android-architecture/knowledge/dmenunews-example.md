# dmenunews Android アーキテクチャガイド

NTTドコモ dメニューニュースアプリのアーキテクチャ設計と実装パターンについて解説します。
新規参加メンバーやコードレビュー時の参考資料として活用してください。

---

## 1. プロジェクト構造と設計思想

### 1.1 モジュール構成

```
docomo-dmenu-news-android/
├── app/                    # アプリケーションモジュール（DI統合、FireBase設定）
├── ui/                     # UI層（Compose画面、ViewModel）
├── domain/                 # ドメイン層（UseCase、Repository Interface、Model）
├── data/                   # データ層（Repository実装、Room、Retrofit、DataStore）
├── analytics/              # 分析・イベント送信
├── allox/                  # 広告SDK統合
├── allox-sdk/              # 広告SDK本体
├── daccount-connect-sdk/   # dアカウント連携SDK
├── baselineprofile/        # パフォーマンス最適化
└── build-logic/            # Gradle Convention Plugins
```

### 1.2 設計思想

**Clean Architecture** を基盤とし、以下の原則に従います：

1. **依存性の方向**: `app` → `ui` → `domain` ← `data`
2. **Domain層の独立性**: Domainはフレームワークに依存しない純粋なKotlinコード
3. **Feature単位のパッケージ分割**: 各層でfeature（機能）ごとにパッケージを分割

```
domain/src/main/kotlin/com/nttdocomo/android/dmenunews/domain/
├── mylist/           # マイリスト機能
│   ├── di/           # DI Module
│   ├── model/        # ドメインモデル
│   ├── repository/   # Repository Interface
│   └── usecase/      # UseCase
├── timeline/         # タイムライン機能
├── account/          # アカウント機能
├── setting/          # 設定機能
└── common/           # 共通機能
```

---

## 2. 採用アーキテクチャ：MVI（Model-View-Intent）

### 2.1 MVIを選択した理由

| 観点 | MVIの利点 |
|------|----------|
| **予測可能性** | 単方向データフロー（Unidirectional Data Flow）により状態遷移が明確 |
| **テスタビリティ** | 純粋関数による状態変換（Reducer）が単体テスト容易 |
| **責務分離** | Intent/Action/State/Eventで役割が明確に分かれる |
| **デバッグ** | 状態の変化を追跡しやすく、Time Travel Debugging可能 |

### 2.2 MVIコンポーネント構成

```
┌─────────────────────────────────────────────────────────────┐
│                         Screen                               │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ collectAsStateWithLifecycle() で State を購読         │ │
│   │ onIntent() で ユーザーアクションを送信                 │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │ Intent
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       ViewModel                              │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ ・StateManager と Presenter を協調制御                │ │
│   │ ・CoroutineScope 管理                                  │ │
│   │ ・ライフサイクル管理                                   │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │ Action
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     StateManager                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ ・Intent → Action 変換                                 │ │
│   │ ・Action の処理振り分け                                │ │
│   │ ・State の保持と更新                                   │ │
│   │ ・Event の発行                                         │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
            │                              │
    純粋な状態変換                      副作用実行
            ▼                              ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│       Reducer        │    │           Presenter              │
│ ┌──────────────────┐ │    │ ┌──────────────────────────────┐ │
│ │ reduce(          │ │    │ │ ・UseCase呼び出し            │ │
│ │   currentState,  │ │    │ │ ・API通信                     │ │
│ │   action         │ │    │ │ ・DB操作                      │ │
│ │ ): NewState      │ │    │ │ ・Analytics送信               │ │
│ └──────────────────┘ │    │ └──────────────────────────────┘ │
└──────────────────────┘    └──────────────────────────────────┘
```

### 2.3 MVI基盤クラス（共通）

プロジェクトでは `ui/common/mvi/` に基盤クラスを定義：

```kotlin
// Intent: ユーザーアクションを表現
interface MviIntent

// Action: 状態変更や副作用実行の指示
interface MviAction

// State: 画面の状態
interface MviState

// Event: 一回限りのイベント（ナビゲーション、Toast等）
interface MviEvent
```

**StateManager** - フロー制御の中核：
```kotlin
abstract class StateManager<I : MviIntent, A : MviAction, S : MviState, E : MviEvent>(
    protected val coroutineScope: CoroutineScope,
    initialState: S,
) {
    protected val _state = MutableStateFlow(initialState)
    val state: StateFlow<S> = _state.asStateFlow()

    protected val _events = MutableSharedFlow<E>()
    val events: SharedFlow<E> = _events.asSharedFlow()

    // Intent を Action リストに変換
    abstract fun processIntent(intent: I): List<A>

    // Action を処理（状態更新 or 副作用実行）
    abstract suspend fun handleAction(action: A)
}
```

**StateReducer** - 純粋な状態変換：
```kotlin
abstract class StateReducer<S : MviState, A : MviAction> {
    // 現在の状態と Action から新しい状態を生成（純粋関数）
    abstract fun reduce(currentState: S, action: A): S
}
```

### 2.4 機能別MVIの実装例（MyList）

**Intent定義**:
```kotlin
sealed interface MyListIntent : MviIntent {
    data object Initialize : MyListIntent
    data class SelectTab(val tab: MyListTab) : MyListIntent
    data class RemoveFavorite(val articleId: String) : MyListIntent
    data class NavigateToArticle(val articleUrl: String) : MyListIntent
}
```

**State定義**:
```kotlin
@Immutable
sealed interface MyListUiState : MviState {
    data object Loading : MyListUiState
    data class Success(
        val selectedTab: MyListTab,
        val favoriteArticles: ImmutableList<FavoriteArticle> = persistentListOf(),
        val browsingHistory: ImmutableList<BrowsingHistory> = persistentListOf(),
    ) : MyListUiState
    data class Error(val message: String) : MyListUiState
}
```

**ViewModel** - 薄いインターフェース層：
```kotlin
@HiltViewModel
class MyListViewModel @Inject constructor(
    private val stateManager: MyListStateManager,
    private val presenter: MyListPresenter,
) : ViewModel() {
    val uiState: StateFlow<MyListUiState> = stateManager.state
    val uiEvent: SharedFlow<MyListUiEvent> = stateManager.events

    fun onIntent(intent: MyListIntent) {
        val actions = stateManager.processIntent(intent)
        viewModelScope.launch {
            actions.forEach { action ->
                when (action) {
                    is MyListAction.RequestInitialLoad -> handleInitialLoad()
                    else -> stateManager.handleAction(action)
                }
            }
        }
    }
}
```

---

## 3. 状態管理の方針

### 3.1 StateFlow による状態保持

```kotlin
// ViewModel側
val uiState: StateFlow<MyListUiState> = stateManager.state

// Compose側
@Composable
fun MyListScreen(viewModel: MyListViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    when (uiState) {
        is MyListUiState.Loading -> LoadingContent()
        is MyListUiState.Success -> SuccessContent(uiState)
        is MyListUiState.Error -> ErrorContent(uiState)
    }
}
```

### 3.2 Immutable State の活用

`kotlinx-collections-immutable` を使用してパフォーマンス最適化：

```kotlin
data class Success(
    val favoriteArticles: ImmutableList<FavoriteArticle> = persistentListOf(),
    val browsingHistory: ImmutableList<BrowsingHistory> = persistentListOf(),
) : MyListUiState
```

### 3.3 Event（一回限りのイベント）

SharedFlow でナビゲーションやToast表示などの一回限りイベントを処理：

```kotlin
// ViewModel
val uiEvent: SharedFlow<MyListUiEvent> = stateManager.events

// Compose
LaunchedEffect(Unit) {
    viewModel.uiEvent.collect { event ->
        when (event) {
            is MyListUiEvent.NavigateToArticle -> onNavigateToArticle(event.articleUrl)
            is MyListUiEvent.ShowToast -> snackbarHostState.showSnackbar(event.message)
        }
    }
}
```

---

## 4. DI構成（Hilt）

### 4.1 DI Module の配置

各レイヤー・機能ごとに Module を分割：

```
data/mylist/di/RepositoryModule.kt    # Repository 実装のバインド
domain/mylist/di/DomainModule.kt      # UseCase のバインド（必要な場合）
ui/feature/mylist/di/MyListMviModule.kt # MVI コンポーネントのバインド
```

### 4.2 Repository の DI

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {
    @Provides
    @Singleton
    fun provideMyListRepository(impl: MyListRepositoryImpl): MyListRepository = impl
}
```

### 4.3 MVI コンポーネントの DI

```kotlin
@Module
@InstallIn(ViewModelComponent::class)
object MyListMviModule {
    @Provides
    @ViewModelScoped
    fun provideMyListStateManager(
        coroutineScope: CoroutineScope,
        reducer: MyListReducer,
    ): MyListStateManager = MyListStateManager(coroutineScope, reducer)
}
```

### 4.4 Scope の使い分け

| Scope | 用途 | 例 |
|-------|------|-----|
| `@Singleton` | アプリ全体で共有 | Repository, DataStore |
| `@ViewModelScoped` | ViewModel のライフサイクルに紐づく | StateManager, Presenter |
| `@ActivityScoped` | Activity のライフサイクルに紐づく | 特定の Activity に依存するもの |

---

## 5. データ層の設計

### 5.1 Repository パターン

**Domain層でInterface定義**:
```kotlin
// domain/mylist/repository/MyListRepository.kt
interface MyListRepository {
    fun streamFavoriteArticles(): Flow<List<FavoriteArticle>>
    suspend fun isFavorite(articleId: String): Result<Boolean>
    suspend fun addFavoriteArticle(article: FavoriteArticle): Result<Unit>
    suspend fun removeFavoriteArticle(articleId: String): Result<Unit>
}
```

**Data層で実装**:
```kotlin
// data/mylist/repository/MyListRepositoryImpl.kt
class MyListRepositoryImpl @Inject constructor(
    private val favoriteArticleDao: FavoriteArticleDao,
    private val browsingHistoryDao: BrowsingHistoryDao,
) : MyListRepository {

    override fun streamFavoriteArticles(): Flow<List<FavoriteArticle>> =
        favoriteArticleDao.streamFavorites().map { list ->
            list.map { entity -> entity.toDomainModel() }
        }

    override suspend fun isFavorite(articleId: String): Result<Boolean> =
        runCatching {
            favoriteArticleDao.exists(articleId)
        }
}
```

### 5.2 UseCase パターン

**one-shot型（単発リクエスト）**:
```kotlin
class GetFavoriteArticleCountUseCase @Inject constructor(
    private val myListRepository: MyListRepository,
) {
    operator fun invoke(): Flow<Int> =
        myListRepository.streamFavoriteArticles().map { it.size }
}
```

**stream型（継続的な購読）**:
```kotlin
interface StreamUserTabUseCase {
    operator fun invoke(): Flow<List<UserTab>>
}
```

### 5.3 Result型によるエラーハンドリング

```kotlin
// Repository
suspend fun removeFavoriteArticle(articleId: String): Result<Unit> =
    runCatching {
        favoriteArticleDao.deleteById(articleId)
    }

// UseCase / Presenter での利用
val result = repository.removeFavoriteArticle(articleId)
result.onSuccess { /* 成功処理 */ }
      .onFailure { /* エラー処理 */ }
```

---

## 6. パッケージ構造の詳細

### 6.1 Domain層

```
domain/src/main/kotlin/.../domain/
└── [feature]/
    ├── di/                  # DI Module（必要な場合）
    ├── model/               # ドメインモデル（純粋なdata class）
    ├── repository/          # Repository Interface
    └── usecase/             # UseCase（ビジネスロジック）
```

### 6.2 Data層

```
data/src/main/kotlin/.../data/
└── [feature]/
    ├── di/                  # DI Module（Repository バインド）
    ├── repository/          # Repository 実装
    ├── entity/              # Room Entity / API Response
    ├── dao/                 # Room DAO
    ├── datasource/          # DataSource（API, Local）
    └── mapper/              # Entity ↔ Model 変換
```

### 6.3 UI層

```
ui/src/main/kotlin/.../ui/
├── common/
│   ├── mvi/                 # MVI 基盤クラス
│   ├── component/           # 共通 Composable
│   ├── theme/               # テーマ設定
│   └── di/                  # 共通 DI Module
└── feature/
    └── [feature]/
        ├── [Feature]Screen.kt      # 画面 Composable
        ├── [Feature]ViewModel.kt   # ViewModel
        ├── [Feature]UiState.kt     # UI State
        ├── [Feature]Intent.kt      # Intent
        ├── [Feature]UiEvent.kt     # Event
        ├── di/                     # MVI DI Module
        └── mvi/
            ├── [Feature]StateManager.kt
            ├── [Feature]Reducer.kt
            ├── [Feature]Presenter.kt
            └── [Feature]Action.kt
```

---

## 7. テスト戦略

### 7.1 各層のテスト方針

| 層 | テスト対象 | アプローチ |
|----|----------|-----------|
| **Reducer** | 純粋関数の状態変換 | 入力/出力の検証（モック不要） |
| **Presenter** | 副作用処理 | UseCase のモックで検証 |
| **UseCase** | ビジネスロジック | Repository のモックで検証 |
| **Repository** | データアクセス | DAO/API のモックまたはIn-Memory DB |
| **Screen** | UI 表示 | Compose Testing + スクリーンショットテスト |

### 7.2 テスト実行コマンド

```bash
# Java環境設定
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"

# 全ビルドバリアントでテスト
./gradlew test

# 特定モジュールのテスト
./gradlew ui:testDevelopDebugUnitTest
./gradlew domain:testDevelopDebugUnitTest
./gradlew data:testDevelopDebugUnitTest
```

---

## 8. 開発フロー

### 8.1 新機能追加の手順

1. **Domain層から設計開始**
   - Model定義
   - Repository Interface定義
   - UseCase定義

2. **Data層で実装**
   - Entity定義
   - DAO実装（Room使用時）
   - Repository実装
   - DI Module作成

3. **UI層で実装**
   - Intent/State/Event定義
   - Reducer実装（純粋な状態変換）
   - Presenter実装（副作用処理）
   - StateManager実装（フロー制御）
   - ViewModel実装（薄いインターフェース）
   - Screen実装（Compose UI）
   - DI Module作成

4. **テスト作成**
   - Reducer単体テスト（必須）
   - UseCase単体テスト
   - 統合テスト

### 8.2 コード品質チェック

```bash
# フォーマット
./gradlew ktlintFormat

# 全テスト実行（CI失敗防止）
./gradlew testDevelopDebugUnitTest
./gradlew testStagingDebugUnitTest
```

---

## 9. よくある質問（FAQ）

### Q1: MVVMとMVIの違いは？

**MVVM**: ViewModel が複数の LiveData/StateFlow を公開。双方向バインディング可能。
**MVI**: 単一の State と単方向データフロー。Intent → Action → State の明確なフロー。

### Q2: すべての画面でMVIを使うべき？

シンプルな画面（設定画面等）では軽量なMVVM風アプローチも可。
複雑な状態管理が必要な画面ではMVIを推奨。

### Q3: Compose と Fragment の使い分けは？

- **Compose**: 全画面、オプションメニュー
- **Fragment**: ダイアログ、ボトムシート（固有のビジネスロジックを持つ場合）

### Q4: UseCaseは必ず必要？

単純なCRUD操作でビジネスロジックがない場合、RepositoryをViewModelから直接呼び出すことも可。
ただし、複数のRepository操作の組み合わせや、ビジネスルールの適用が必要な場合はUseCaseを作成。

---

## 10. 参考リソース

- [Android Architecture Components](https://developer.android.com/topic/architecture)
- [Jetpack Compose State](https://developer.android.com/jetpack/compose/state)
- [MVI Architecture Guide](https://developer.android.com/jetpack/guide/ui-layer)
- プロジェクト内ナレッジ: `.cursor/knowledge/` ディレクトリ
