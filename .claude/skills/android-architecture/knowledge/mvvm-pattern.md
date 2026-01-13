# MVVM パターン詳細ガイド

Model-View-ViewModel（MVVM）パターンの詳細な解説と実装ガイドです。

---

## 1. MVVMとは

### 1.1 概要

MVVMは**シンプルな状態管理**を実現するアーキテクチャパターンです。

```
User Action → ViewModel → State → View → User Action → ...
```

### 1.2 MVIとの違い

| 観点 | MVVM | MVI |
|------|------|-----|
| データフロー | シンプル | 厳密な単方向 |
| 状態管理 | UiState（1つ） | Intent → Action → State |
| 学習コスト | 低 | 中〜高 |
| ボイラープレート | 少 | 多 |
| 適したケース | シンプルな画面 | 複雑な状態管理 |

### 1.3 MVVMを選ぶべき場面

**推奨**:
- 5-10画面程度のアプリ
- CRUD中心の画面
- チームにMVI経験者がいない
- 短期間でのリリースが必要

**非推奨**:
- 複数画面で状態を共有する複雑なアプリ
- 厳密な状態遷移の追跡が必要
- 大規模チームでの開発

---

## 2. MVVMの構成要素

### 2.1 UiState（画面状態）

画面の現在の状態を表現します。

```kotlin
@Immutable
sealed interface ArticleUiState {
    data object Loading : ArticleUiState

    data class Success(
        val articles: ImmutableList<Article> = persistentListOf(),
        val isRefreshing: Boolean = false,
    ) : ArticleUiState

    data class Error(
        val message: String,
    ) : ArticleUiState
}
```

**設計原則**:
- Immutableにする（`@Immutable`, `ImmutableList`）
- 画面に必要な情報をすべて含める
- sealed interfaceで状態を網羅的に定義

### 2.2 UiEvent（一回限りイベント）

ナビゲーション、Toast等の一回限りの通知を表現します。

```kotlin
sealed interface ArticleUiEvent {
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

## 3. ViewModel実装

### 3.1 基底クラス（オプション）

```kotlin
// ui/common/BaseViewModel.kt
abstract class BaseViewModel<S, E>(
    initialState: S,
) : ViewModel() {

    protected val _uiState = MutableStateFlow(initialState)
    val uiState: StateFlow<S> = _uiState.asStateFlow()

    protected val _uiEvent = MutableSharedFlow<E>(replay = 0)
    val uiEvent: SharedFlow<E> = _uiEvent.asSharedFlow()

    protected fun updateState(reducer: S.() -> S) {
        _uiState.update { it.reducer() }
    }

    protected fun emitEvent(event: E) {
        viewModelScope.launch {
            _uiEvent.emit(event)
        }
    }
}
```

### 3.2 具体的なViewModel

```kotlin
@HiltViewModel
class ArticleViewModel @Inject constructor(
    private val getArticlesUseCase: GetArticlesUseCase,
    private val toggleFavoriteUseCase: ToggleFavoriteUseCase,
) : BaseViewModel<ArticleUiState, ArticleUiEvent>(
    initialState = ArticleUiState.Loading
) {

    init {
        loadArticles()
    }

    fun loadArticles() {
        viewModelScope.launch {
            updateState { ArticleUiState.Loading }

            getArticlesUseCase()
                .onSuccess { articles ->
                    updateState {
                        ArticleUiState.Success(
                            articles = articles.toImmutableList()
                        )
                    }
                }
                .onFailure { error ->
                    updateState {
                        ArticleUiState.Error(
                            message = error.message ?: "Unknown error"
                        )
                    }
                }
        }
    }

    fun onArticleClick(articleId: String) {
        emitEvent(ArticleUiEvent.NavigateToDetail(articleId))
    }

    fun onToggleFavorite(articleId: String) {
        viewModelScope.launch {
            toggleFavoriteUseCase(articleId)
                .onSuccess {
                    loadArticles() // 再読み込み
                }
                .onFailure { error ->
                    emitEvent(ArticleUiEvent.ShowToast(error.message ?: "Failed"))
                }
        }
    }

    fun onRefresh() {
        viewModelScope.launch {
            val currentState = _uiState.value
            if (currentState is ArticleUiState.Success) {
                updateState { currentState.copy(isRefreshing = true) }
            }

            getArticlesUseCase()
                .onSuccess { articles ->
                    updateState {
                        ArticleUiState.Success(
                            articles = articles.toImmutableList(),
                            isRefreshing = false
                        )
                    }
                }
                .onFailure { error ->
                    updateState {
                        ArticleUiState.Error(message = error.message ?: "Unknown error")
                    }
                }
        }
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
        onArticleClick = viewModel::onArticleClick,
        onToggleFavorite = viewModel::onToggleFavorite,
        onRefresh = viewModel::onRefresh,
        onRetry = viewModel::loadArticles,
    )
}

@Composable
private fun ArticleContent(
    uiState: ArticleUiState,
    onArticleClick: (String) -> Unit,
    onToggleFavorite: (String) -> Unit,
    onRefresh: () -> Unit,
    onRetry: () -> Unit,
) {
    when (uiState) {
        is ArticleUiState.Loading -> {
            LoadingIndicator()
        }
        is ArticleUiState.Success -> {
            SwipeRefresh(
                isRefreshing = uiState.isRefreshing,
                onRefresh = onRefresh,
            ) {
                ArticleList(
                    articles = uiState.articles,
                    onArticleClick = onArticleClick,
                    onFavoriteClick = onToggleFavorite,
                )
            }
        }
        is ArticleUiState.Error -> {
            ErrorContent(
                message = uiState.message,
                onRetry = onRetry,
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
        onArticleClick = {},
        onToggleFavorite = {},
        onRefresh = {},
        onRetry = {},
    )
}

@Preview
@Composable
private fun ArticleContentLoadingPreview() {
    ArticleContent(
        uiState = ArticleUiState.Loading,
        onArticleClick = {},
        onToggleFavorite = {},
        onRefresh = {},
        onRetry = {},
    )
}
```

---

## 5. ディレクトリ構造

### 5.1 by-feature構造（推奨）

```
ui/
├── common/
│   ├── BaseViewModel.kt
│   ├── UiState.kt          # マーカーインターフェース（オプション）
│   └── UiEvent.kt          # マーカーインターフェース（オプション）
└── feature/
    ├── article/
    │   ├── ArticleScreen.kt
    │   ├── ArticleViewModel.kt
    │   ├── ArticleUiState.kt
    │   ├── ArticleUiEvent.kt
    │   └── components/
    │       ├── ArticleList.kt
    │       └── ArticleCard.kt
    └── setting/
        ├── SettingScreen.kt
        ├── SettingViewModel.kt
        └── SettingUiState.kt
```

### 5.2 DI設定（Hilt）

```kotlin
// 特別なModuleは不要
// ViewModelは @HiltViewModel アノテーションのみでOK

@HiltViewModel
class ArticleViewModel @Inject constructor(
    private val getArticlesUseCase: GetArticlesUseCase,
) : ViewModel() {
    // ...
}
```

---

## 6. テスト戦略

### 6.1 ViewModelテスト

```kotlin
class ArticleViewModelTest {

    @MockK
    private lateinit var getArticlesUseCase: GetArticlesUseCase

    private lateinit var viewModel: ArticleViewModel

    @Before
    fun setup() {
        MockKAnnotations.init(this)
    }

    @Test
    fun `loadArticles should emit Success state`() = runTest {
        // Given
        val articles = listOf(Article("1", "Title"))
        coEvery { getArticlesUseCase() } returns Result.success(articles)

        // When
        viewModel = ArticleViewModel(getArticlesUseCase)
        advanceUntilIdle()

        // Then
        assertThat(viewModel.uiState.value)
            .isInstanceOf(ArticleUiState.Success::class.java)
    }

    @Test
    fun `loadArticles should emit Error state on failure`() = runTest {
        // Given
        coEvery { getArticlesUseCase() } returns Result.failure(Exception("Network error"))

        // When
        viewModel = ArticleViewModel(getArticlesUseCase)
        advanceUntilIdle()

        // Then
        assertThat(viewModel.uiState.value)
            .isInstanceOf(ArticleUiState.Error::class.java)
    }

    @Test
    fun `onArticleClick should emit NavigateToDetail event`() = runTest {
        // Given
        coEvery { getArticlesUseCase() } returns Result.success(emptyList())
        viewModel = ArticleViewModel(getArticlesUseCase)

        val events = mutableListOf<ArticleUiEvent>()
        val job = launch {
            viewModel.uiEvent.collect { events.add(it) }
        }

        // When
        viewModel.onArticleClick("123")
        advanceUntilIdle()

        // Then
        assertThat(events).contains(ArticleUiEvent.NavigateToDetail("123"))
        job.cancel()
    }
}
```

---

## 7. MVIへの移行パス

MVVMで始めて、必要に応じてMVIに移行できます。

### 7.1 移行のタイミング

- 状態管理のバグが増えてきた
- 複数のコルーチンが状態を更新して競合が発生
- デバッグが困難になってきた

### 7.2 移行手順

1. UiStateはそのまま使える
2. ViewModelの関数をIntentに置き換え
3. Reducer, Presenterを分離
4. StateManagerを導入

詳細は `migration-guide.md` を参照。

---

## 8. よくある質問

### Q1: BaseViewModelは必須？

いいえ。シンプルなプロジェクトなら不要です。各ViewModelで直接StateFlowを定義してもOK。

### Q2: UiEventとSnackbarの違いは？

UiEventは一回限りの通知全般。Snackbarだけでなく、ナビゲーション、ダイアログ表示なども含みます。

### Q3: リフレッシュ中の状態管理は？

Success状態のプロパティとして`isRefreshing`を持つのがシンプル。Loading状態とは分けることで、既存のリストを表示したままリフレッシュできます。

### Q4: 複数のUseCaseを呼ぶ場合は？

ViewModelで直接呼び出してOK。MVIのようにActionを分離する必要はありません。

```kotlin
fun loadData() {
    viewModelScope.launch {
        updateState { UiState.Loading }

        val articles = async { getArticlesUseCase() }
        val categories = async { getCategoriesUseCase() }

        // 両方の結果を待つ
        val articlesResult = articles.await()
        val categoriesResult = categories.await()

        // 結果を反映
        // ...
    }
}
```

---

## 9. 参考資料

- [Android Architecture Components](https://developer.android.com/topic/architecture)
- [MVIパターンガイド](./mvi-pattern.md)
- [移行ガイド](./migration-guide.md)

---

**作成日**: 2026-01-13
**作成者**: Claude Code（android-architectureスキル）
