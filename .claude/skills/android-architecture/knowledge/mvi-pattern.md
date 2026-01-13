# MVI パターン詳細ガイド

Model-View-Intent（MVI）パターンの詳細な解説と実装ガイドです。

---

## 1. MVIとは

### 1.1 概要

MVIは**単方向データフロー**（Unidirectional Data Flow）を実現するアーキテクチャパターンです。

```
User Action → Intent → Model → View → User Action → ...
```

### 1.2 MVVMとの違い

| 観点 | MVVM | MVI |
|------|------|-----|
| データフロー | 双方向可能 | 単方向のみ |
| 状態管理 | 複数のLiveData/StateFlow | 単一のState |
| 複雑性 | シンプル | やや複雑 |
| 予測可能性 | 中 | 高 |
| テスタビリティ | 中 | 高 |
| 適したケース | シンプルな画面 | 複雑な状態管理 |

### 1.3 MVIを選ぶべき場面

**推奨**:
- 複数の状態が相互に影響する画面
- ユーザー操作が多い画面
- 状態遷移のデバッグが重要な場面
- チーム開発で一貫性が必要な場合

**非推奨**:
- 単純なCRUD画面
- 状態がほぼ固定の画面
- プロトタイプや短期プロジェクト

---

## 2. MVIの構成要素

### 2.1 Intent（意図）

ユーザーの操作や外部イベントを表現します。

```kotlin
sealed interface ArticleIntent : MviIntent {
    data object LoadArticles : ArticleIntent
    data class SelectArticle(val id: String) : ArticleIntent
    data class ToggleFavorite(val id: String) : ArticleIntent
    data object Refresh : ArticleIntent
}
```

**設計原則**:
- ユーザー視点で命名（「何をしたいか」）
- 1つのIntentは1つの操作を表す
- データは最小限に（IDのみ等）

### 2.2 Action（アクション）

システム内部の処理を表現します。Intentから変換されます。

```kotlin
sealed interface ArticleAction : MviAction {
    // 状態変更系
    data object ShowLoading : ArticleAction
    data class UpdateArticles(val articles: List<Article>) : ArticleAction
    data class ShowError(val message: String) : ArticleAction

    // 副作用系
    data object RequestLoadArticles : ArticleAction
    data class RequestToggleFavorite(val id: String) : ArticleAction
}
```

**設計原則**:
- システム視点で命名（「何をするか」）
- 状態変更と副作用を明確に分離
- 1つのIntentが複数のActionに展開されることもある

### 2.3 State（状態）

画面の現在の状態を表現します。

```kotlin
@Immutable
sealed interface ArticleUiState : MviState {
    data object Loading : ArticleUiState

    data class Success(
        val articles: ImmutableList<Article> = persistentListOf(),
        val selectedArticleId: String? = null,
        val isRefreshing: Boolean = false,
    ) : ArticleUiState

    data class Error(
        val message: String,
        val canRetry: Boolean = true,
    ) : ArticleUiState
}
```

**設計原則**:
- Immutableにする（`@Immutable`, `ImmutableList`）
- 画面に必要な情報をすべて含める
- sealed interfaceで状態を網羅的に定義

### 2.4 Event（イベント）

一回限りの通知（ナビゲーション、Toast等）を表現します。

```kotlin
sealed interface ArticleUiEvent : MviEvent {
    data class NavigateToDetail(val articleId: String) : ArticleUiEvent
    data class ShowToast(val message: String) : ArticleUiEvent
    data object NavigateBack : ArticleUiEvent
}
```

**設計原則**:
- Stateに含めない（消費されたら消える）
- SharedFlowで実装（replay = 0）
- UIでのみ消費される

---

## 3. コンポーネント実装

### 3.1 Reducer（状態変換）

**純粋関数**として実装。テストが最も容易。

```kotlin
class ArticleReducer : StateReducer<ArticleUiState, ArticleAction>() {

    override fun reduce(
        currentState: ArticleUiState,
        action: ArticleAction
    ): ArticleUiState {
        return when (action) {
            is ArticleAction.ShowLoading -> ArticleUiState.Loading

            is ArticleAction.UpdateArticles -> {
                ArticleUiState.Success(
                    articles = action.articles.toImmutableList()
                )
            }

            is ArticleAction.ShowError -> {
                ArticleUiState.Error(message = action.message)
            }

            // 副作用系Actionは状態を変えない
            is ArticleAction.RequestLoadArticles,
            is ArticleAction.RequestToggleFavorite -> currentState
        }
    }
}
```

**テスト例**:
```kotlin
@Test
fun `UpdateArticles should transition to Success state`() {
    val reducer = ArticleReducer()
    val articles = listOf(Article("1", "Title"))

    val newState = reducer.reduce(
        ArticleUiState.Loading,
        ArticleAction.UpdateArticles(articles)
    )

    assertThat(newState).isInstanceOf(ArticleUiState.Success::class.java)
    assertThat((newState as ArticleUiState.Success).articles).hasSize(1)
}
```

### 3.2 Presenter（副作用処理）

UseCase呼び出し、API通信などの副作用を担当。

```kotlin
class ArticlePresenter @Inject constructor(
    private val getArticlesUseCase: GetArticlesUseCase,
    private val toggleFavoriteUseCase: ToggleFavoriteUseCase,
) {
    suspend fun loadArticles(): Result<List<Article>> {
        return getArticlesUseCase()
    }

    suspend fun toggleFavorite(articleId: String): Result<Unit> {
        return toggleFavoriteUseCase(articleId)
    }
}
```

**設計原則**:
- UseCaseを注入して使う
- Result型でエラーを返す
- 状態は持たない（Stateless）

### 3.3 StateManager（フロー制御）

Intent → Action変換と、Action処理の振り分けを担当。

```kotlin
class ArticleStateManager @Inject constructor(
    coroutineScope: CoroutineScope,
    private val reducer: ArticleReducer,
    private val presenter: ArticlePresenter,
) : StateManager<ArticleIntent, ArticleAction, ArticleUiState, ArticleUiEvent>(
    coroutineScope = coroutineScope,
    initialState = ArticleUiState.Loading,
) {
    override fun processIntent(intent: ArticleIntent): List<ArticleAction> {
        return when (intent) {
            is ArticleIntent.LoadArticles -> listOf(
                ArticleAction.ShowLoading,
                ArticleAction.RequestLoadArticles
            )
            is ArticleIntent.SelectArticle -> listOf(
                ArticleAction.SelectArticle(intent.id)
            )
            is ArticleIntent.ToggleFavorite -> listOf(
                ArticleAction.RequestToggleFavorite(intent.id)
            )
            is ArticleIntent.Refresh -> listOf(
                ArticleAction.RequestLoadArticles
            )
        }
    }

    override suspend fun handleAction(action: ArticleAction) {
        when (action) {
            // 状態変更系 → Reducerに委譲
            is ArticleAction.ShowLoading,
            is ArticleAction.UpdateArticles,
            is ArticleAction.ShowError -> {
                _state.value = reducer.reduce(_state.value, action)
            }

            // 副作用系 → Presenterに委譲
            is ArticleAction.RequestLoadArticles -> {
                presenter.loadArticles()
                    .onSuccess { articles ->
                        handleAction(ArticleAction.UpdateArticles(articles))
                    }
                    .onFailure { error ->
                        handleAction(ArticleAction.ShowError(error.message ?: "Unknown error"))
                    }
            }

            is ArticleAction.RequestToggleFavorite -> {
                presenter.toggleFavorite(action.id)
                    .onSuccess {
                        // 再読み込み or 部分更新
                        handleAction(ArticleAction.RequestLoadArticles)
                    }
                    .onFailure { error ->
                        _events.emit(ArticleUiEvent.ShowToast(error.message ?: "Failed"))
                    }
            }
        }
    }
}
```

### 3.4 ViewModel（薄いインターフェース）

AndroidのViewModelとして、StateManagerをラップ。

```kotlin
@HiltViewModel
class ArticleViewModel @Inject constructor(
    private val stateManager: ArticleStateManager,
) : ViewModel() {

    val uiState: StateFlow<ArticleUiState> = stateManager.state
    val uiEvent: SharedFlow<ArticleUiEvent> = stateManager.events

    fun onIntent(intent: ArticleIntent) {
        viewModelScope.launch {
            val actions = stateManager.processIntent(intent)
            actions.forEach { action ->
                stateManager.handleAction(action)
            }
        }
    }

    init {
        onIntent(ArticleIntent.LoadArticles)
    }
}
```

---

## 4. Compose UIでの利用

### 4.1 基本パターン

```kotlin
@Composable
fun ArticleScreen(
    viewModel: ArticleViewModel = hiltViewModel(),
    onNavigateToDetail: (String) -> Unit,
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // Event処理
    LaunchedEffect(Unit) {
        viewModel.uiEvent.collect { event ->
            when (event) {
                is ArticleUiEvent.NavigateToDetail -> {
                    onNavigateToDetail(event.articleId)
                }
                is ArticleUiEvent.ShowToast -> {
                    // Snackbar表示
                }
                is ArticleUiEvent.NavigateBack -> {
                    // 戻る処理
                }
            }
        }
    }

    // State描画
    ArticleContent(
        uiState = uiState,
        onIntent = viewModel::onIntent,
    )
}

@Composable
private fun ArticleContent(
    uiState: ArticleUiState,
    onIntent: (ArticleIntent) -> Unit,
) {
    when (uiState) {
        is ArticleUiState.Loading -> {
            LoadingIndicator()
        }
        is ArticleUiState.Success -> {
            ArticleList(
                articles = uiState.articles,
                onArticleClick = { id ->
                    onIntent(ArticleIntent.SelectArticle(id))
                },
                onFavoriteClick = { id ->
                    onIntent(ArticleIntent.ToggleFavorite(id))
                },
            )
        }
        is ArticleUiState.Error -> {
            ErrorContent(
                message = uiState.message,
                onRetry = { onIntent(ArticleIntent.LoadArticles) },
            )
        }
    }
}
```

### 4.2 Preview対応

```kotlin
@Preview
@Composable
private fun ArticleContentSuccessPreview() {
    ArticleContent(
        uiState = ArticleUiState.Success(
            articles = persistentListOf(
                Article("1", "Sample Article 1"),
                Article("2", "Sample Article 2"),
            )
        ),
        onIntent = {},
    )
}

@Preview
@Composable
private fun ArticleContentLoadingPreview() {
    ArticleContent(
        uiState = ArticleUiState.Loading,
        onIntent = {},
    )
}
```

---

## 5. テスト戦略

### 5.1 各コンポーネントのテスト

| コンポーネント | テスト容易性 | モック必要性 |
|--------------|------------|-------------|
| Reducer | ★★★ 最も容易 | 不要 |
| Presenter | ★★☆ 容易 | UseCase |
| StateManager | ★★☆ 容易 | Presenter |
| ViewModel | ★☆☆ やや複雑 | StateManager |

### 5.2 Reducerテスト（推奨）

```kotlin
class ArticleReducerTest {
    private val reducer = ArticleReducer()

    @Test
    fun `ShowLoading should return Loading state`() {
        val result = reducer.reduce(
            ArticleUiState.Success(),
            ArticleAction.ShowLoading
        )
        assertThat(result).isEqualTo(ArticleUiState.Loading)
    }

    @Test
    fun `UpdateArticles should preserve other state properties`() {
        val currentState = ArticleUiState.Success(
            selectedArticleId = "123",
            isRefreshing = true,
        )
        val articles = listOf(Article("1", "Title"))

        val result = reducer.reduce(
            currentState,
            ArticleAction.UpdateArticles(articles)
        )

        assertThat(result).isInstanceOf(ArticleUiState.Success::class.java)
        // 必要に応じて他のプロパティも検証
    }
}
```

### 5.3 StateManagerテスト

```kotlin
class ArticleStateManagerTest {
    @MockK
    private lateinit var presenter: ArticlePresenter

    private lateinit var stateManager: ArticleStateManager

    @Before
    fun setup() {
        MockKAnnotations.init(this)
        stateManager = ArticleStateManager(
            coroutineScope = TestScope(),
            reducer = ArticleReducer(),
            presenter = presenter,
        )
    }

    @Test
    fun `LoadArticles intent should emit Loading then Success`() = runTest {
        val articles = listOf(Article("1", "Title"))
        coEvery { presenter.loadArticles() } returns Result.success(articles)

        stateManager.processIntent(ArticleIntent.LoadArticles)
            .forEach { action -> stateManager.handleAction(action) }

        assertThat(stateManager.state.value)
            .isInstanceOf(ArticleUiState.Success::class.java)
    }
}
```

---

## 6. よくある質問

### Q1: Intent と Action の違いは？

**Intent**: ユーザー視点（「記事を読み込みたい」）
**Action**: システム視点（「ローディング表示」「API呼び出し」「結果反映」）

1つのIntentが複数のActionに展開されることがあります。

### Q2: すべてのActionにReducerが反応すべき？

いいえ。副作用系Action（RequestXxx）はReducerで状態を変えず、そのまま返します。

### Q3: Eventはいつ使う？

- ナビゲーション
- Toast/Snackbar表示
- ダイアログ表示
- 一回限りのフィードバック

Stateに含めると「消費済み」の管理が複雑になるため、Eventで分離します。

### Q4: StateManagerとViewModelを分ける理由は？

- テスタビリティ向上（StateManagerは純粋なKotlinクラス）
- 責務分離（ViewModelはAndroidライフサイクル管理のみ）
- 再利用性（StateManagerは他のViewModelでも使える）

---

## 7. 参考資料

- [MVI Architecture for Android](https://developer.android.com/jetpack/guide/ui-layer)
- [Orbit MVI](https://orbit-mvi.org/)（参考ライブラリ）
- [dmenunews実装例](./dmenunews-example.md)
