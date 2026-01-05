# Android UIコーディングガイドライン

## 1. 基本原則

### 1.1 宣言的UIの考え方
Jetpack Composeは宣言的UIフレームワークです。「どのように描画するか」ではなく「何を表示するか」を記述します。

```kotlin
// ✅ 宣言的: 状態に基づいてUIを記述
@Composable
fun UserProfile(user: User) {
    Column {
        Text(text = user.name)
        Text(text = user.email)
    }
}

// ❌ 命令的: UIを手続き的に操作（従来のView方式）
fun updateUserProfile(user: User) {
    nameTextView.text = user.name
    emailTextView.text = user.email
}
```

### 1.2 単一方向データフロー (UDF)
状態は上から下へ流れ、イベントは下から上へ伝播します。

```kotlin
@Composable
fun CounterScreen(
    count: Int,              // State flows down
    onIncrement: () -> Unit  // Events flow up
) {
    Column {
        Text("Count: $count")
        Button(onClick = onIncrement) {
            Text("Increment")
        }
    }
}
```

### 1.3 状態ホイスティング (State Hoisting)
状態を上位のComposableに持ち上げ、コンポーネントをステートレスにします。

```kotlin
// ✅ ステートレスComposable（推奨）
@Composable
fun TextField(
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier
    )
}

// 状態を保持する親Composable
@Composable
fun SearchBar() {
    var query by remember { mutableStateOf("") }
    TextField(
        value = query,
        onValueChange = { query = it }
    )
}
```

---

## 2. Composable設計

### 2.1 命名規則

#### Composable関数
```kotlin
// ✅ PascalCase、名詞または名詞句
@Composable
fun UserProfileCard() { }

@Composable
fun ArticleListItem() { }

@Composable
fun LoadingIndicator() { }

// ❌ 動詞で始めない、小文字で始めない
@Composable
fun showUserProfile() { }  // NG

@Composable
fun userCard() { }  // NG
```

#### パラメータ順序
```kotlin
@Composable
fun CustomButton(
    // 1. 必須パラメータ
    text: String,
    onClick: () -> Unit,
    // 2. オプショナルパラメータ（デフォルト値あり）
    enabled: Boolean = true,
    // 3. Modifier（常にデフォルト値 Modifier）
    modifier: Modifier = Modifier,
    // 4. コンテンツラムダ（最後に配置）
    icon: @Composable (() -> Unit)? = null
) {
    // 実装
}
```

### 2.2 Modifierの使い方

#### 基本ルール
```kotlin
@Composable
fun MyComponent(
    modifier: Modifier = Modifier  // 常にデフォルト値を設定
) {
    // ✅ 渡されたmodifierを最上位要素に適用
    Box(modifier = modifier) {
        // 内部要素には新しいmodifierを使用
        Text(
            text = "Hello",
            modifier = Modifier.padding(16.dp)
        )
    }
}
```

#### Modifierチェーンの順序
```kotlin
// Modifierは順序が重要（適用順に処理される）
Box(
    modifier = Modifier
        .padding(16.dp)      // 外側のpadding
        .background(Color.Blue)
        .padding(8.dp)       // 内側のpadding（背景色の内側）
        .clickable { }
)
```

### 2.3 コンポーネント分割の粒度

#### 分割の基準
1. **再利用性**: 複数箇所で使用される
2. **責務の明確化**: 単一の責務を持つ
3. **テスタビリティ**: 個別にテスト可能
4. **可読性**: 100行を超える場合は分割を検討

```kotlin
// ✅ 適切な粒度で分割
@Composable
fun ArticleCard(
    article: Article,
    onBookmarkClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier) {
        Column {
            ArticleThumbnail(imageUrl = article.imageUrl)
            ArticleContent(
                title = article.title,
                summary = article.summary
            )
            ArticleFooter(
                publishDate = article.publishDate,
                isBookmarked = article.isBookmarked,
                onBookmarkClick = onBookmarkClick
            )
        }
    }
}

@Composable
private fun ArticleThumbnail(imageUrl: String) { /* ... */ }

@Composable
private fun ArticleContent(title: String, summary: String) { /* ... */ }

@Composable
private fun ArticleFooter(
    publishDate: String,
    isBookmarked: Boolean,
    onBookmarkClick: () -> Unit
) { /* ... */ }
```

### 2.4 ファイル/ディレクトリ構成

```
ui/
├── components/           # 再利用可能なUIコンポーネント
│   ├── button/
│   │   ├── PrimaryButton.kt
│   │   └── SecondaryButton.kt
│   ├── card/
│   │   └── ContentCard.kt
│   └── loading/
│       └── LoadingIndicator.kt
│
├── feature/              # 機能別画面
│   ├── home/
│   │   ├── HomeScreen.kt
│   │   ├── HomeViewModel.kt
│   │   ├── HomeUiState.kt
│   │   └── components/   # 画面固有のコンポーネント
│   │       └── HomeHeader.kt
│   └── detail/
│       ├── DetailScreen.kt
│       └── DetailViewModel.kt
│
├── theme/                # テーマ関連
│   ├── Theme.kt
│   ├── Color.kt
│   ├── Typography.kt
│   └── Shape.kt
│
└── navigation/           # ナビゲーション
    └── NavGraph.kt
```

---

## 3. State管理

### 3.1 状態の種類と選択

```kotlin
// UI要素の状態（短命、UIローカル）
@Composable
fun ExpandableCard() {
    var expanded by remember { mutableStateOf(false) }
    // ...
}

// 画面の状態（ViewModel管理）
class HomeViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()
}

// アプリ全体の状態（Repository/DataStore）
class UserPreferencesRepository(
    private val dataStore: DataStore<Preferences>
) {
    val darkModeEnabled: Flow<Boolean> = dataStore.data
        .map { it[DARK_MODE_KEY] ?: false }
}
```

### 3.2 UiState設計

```kotlin
// ✅ Sealed interface/classで状態を明確に
sealed interface HomeUiState {
    data object Loading : HomeUiState
    data class Success(
        val articles: List<Article>,
        val isRefreshing: Boolean = false
    ) : HomeUiState
    data class Error(val message: String) : HomeUiState
}

// ✅ 複合的な状態の場合はdata classで管理
data class FormUiState(
    val name: String = "",
    val email: String = "",
    val nameError: String? = null,
    val emailError: String? = null,
    val isSubmitting: Boolean = false,
    val isValid: Boolean = false
)
```

### 3.3 ViewModelとの連携

```kotlin
@Composable
fun HomeScreen(
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    HomeContent(
        uiState = uiState,
        onRefresh = viewModel::refresh,
        onArticleClick = viewModel::onArticleClick
    )
}

// Stateless Composableとして分離
@Composable
private fun HomeContent(
    uiState: HomeUiState,
    onRefresh: () -> Unit,
    onArticleClick: (Article) -> Unit
) {
    when (uiState) {
        is HomeUiState.Loading -> LoadingIndicator()
        is HomeUiState.Success -> ArticleList(
            articles = uiState.articles,
            onArticleClick = onArticleClick
        )
        is HomeUiState.Error -> ErrorMessage(message = uiState.message)
    }
}
```

### 3.4 Side Effects

```kotlin
@Composable
fun SearchScreen(viewModel: SearchViewModel) {
    val query by viewModel.query.collectAsStateWithLifecycle()

    // ✅ LaunchedEffect: Composable内で非同期処理
    LaunchedEffect(query) {
        if (query.length >= 2) {
            delay(300) // デバウンス
            viewModel.search(query)
        }
    }

    // ✅ DisposableEffect: クリーンアップが必要な処理
    DisposableEffect(Unit) {
        val listener = object : SomeListener { /* ... */ }
        someService.addListener(listener)
        onDispose {
            someService.removeListener(listener)
        }
    }

    // ✅ SideEffect: 毎回のRecompositionで実行
    SideEffect {
        analytics.trackScreenView("SearchScreen")
    }
}
```

---

## 4. 実装パターン

### 4.1 リスト表示

```kotlin
@Composable
fun ArticleList(
    articles: List<Article>,
    onArticleClick: (Article) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(
            items = articles,
            key = { it.id }  // ✅ keyを指定してパフォーマンス向上
        ) { article ->
            ArticleCard(
                article = article,
                onClick = { onArticleClick(article) }
            )
        }
    }
}

// ページング対応
@Composable
fun PagingArticleList(
    articles: LazyPagingItems<Article>,
    onArticleClick: (Article) -> Unit
) {
    LazyColumn {
        items(
            count = articles.itemCount,
            key = articles.itemKey { it.id }
        ) { index ->
            articles[index]?.let { article ->
                ArticleCard(
                    article = article,
                    onClick = { onArticleClick(article) }
                )
            }
        }

        // ローディング表示
        when (articles.loadState.append) {
            is LoadState.Loading -> {
                item { LoadingIndicator() }
            }
            is LoadState.Error -> {
                item { RetryButton(onClick = { articles.retry() }) }
            }
            else -> { }
        }
    }
}
```

### 4.2 フォーム入力

```kotlin
@Composable
fun LoginForm(
    uiState: LoginUiState,
    onEmailChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onSubmit: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        OutlinedTextField(
            value = uiState.email,
            onValueChange = onEmailChange,
            label = { Text("メールアドレス") },
            isError = uiState.emailError != null,
            supportingText = uiState.emailError?.let { { Text(it) } },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Email,
                imeAction = ImeAction.Next
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        OutlinedTextField(
            value = uiState.password,
            onValueChange = onPasswordChange,
            label = { Text("パスワード") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = { onSubmit() }
            ),
            singleLine = true,
            modifier = Modifier.fillMaxWidth()
        )

        Button(
            onClick = onSubmit,
            enabled = uiState.isValid && !uiState.isSubmitting,
            modifier = Modifier.fillMaxWidth()
        ) {
            if (uiState.isSubmitting) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("ログイン")
            }
        }
    }
}
```

### 4.3 ナビゲーション

```kotlin
// NavGraph定義
@Composable
fun AppNavGraph(
    navController: NavHostController = rememberNavController()
) {
    NavHost(
        navController = navController,
        startDestination = "home"
    ) {
        composable("home") {
            HomeScreen(
                onNavigateToDetail = { articleId ->
                    navController.navigate("detail/$articleId")
                }
            )
        }

        composable(
            route = "detail/{articleId}",
            arguments = listOf(
                navArgument("articleId") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val articleId = backStackEntry.arguments?.getString("articleId")
            DetailScreen(
                articleId = articleId,
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}

// Type-safe Navigation（推奨）
@Serializable
data object Home

@Serializable
data class Detail(val articleId: String)

@Composable
fun TypeSafeNavGraph() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = Home) {
        composable<Home> {
            HomeScreen(
                onNavigateToDetail = { articleId ->
                    navController.navigate(Detail(articleId))
                }
            )
        }
        composable<Detail> { backStackEntry ->
            val detail: Detail = backStackEntry.toRoute()
            DetailScreen(articleId = detail.articleId)
        }
    }
}
```

### 4.4 エラーハンドリング

```kotlin
@Composable
fun ContentWithError(
    uiState: ContentUiState,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier.fillMaxSize()) {
        when (uiState) {
            is ContentUiState.Loading -> {
                CircularProgressIndicator(
                    modifier = Modifier.align(Alignment.Center)
                )
            }
            is ContentUiState.Success -> {
                Content(data = uiState.data)
            }
            is ContentUiState.Error -> {
                ErrorContent(
                    message = uiState.message,
                    onRetry = onRetry,
                    modifier = Modifier.align(Alignment.Center)
                )
            }
        }
    }
}

@Composable
private fun ErrorContent(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Icon(
            imageVector = Icons.Default.Error,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.error,
            modifier = Modifier.size(48.dp)
        )
        Text(
            text = message,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )
        Button(onClick = onRetry) {
            Text("再試行")
        }
    }
}
```

### 4.5 ローディング状態

```kotlin
// Pull-to-Refresh
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RefreshableContent(
    isRefreshing: Boolean,
    onRefresh: () -> Unit,
    content: @Composable () -> Unit
) {
    val pullToRefreshState = rememberPullToRefreshState()

    PullToRefreshBox(
        isRefreshing = isRefreshing,
        onRefresh = onRefresh,
        state = pullToRefreshState
    ) {
        content()
    }
}

// Skeleton Loading
@Composable
fun ArticleCardSkeleton(
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "skeleton")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.7f,
        animationSpec = infiniteRepeatable(
            animation = tween(1000),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )

    Card(modifier = modifier) {
        Column(modifier = Modifier.padding(16.dp)) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(120.dp)
                    .background(Color.Gray.copy(alpha = alpha))
            )
            Spacer(modifier = Modifier.height(8.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.8f)
                    .height(20.dp)
                    .background(Color.Gray.copy(alpha = alpha))
            )
        }
    }
}

// コンテンツ表示の切り替え
@Composable
fun ArticleListWithLoading(
    uiState: ArticleListUiState
) {
    when (uiState) {
        is ArticleListUiState.Loading -> {
            LazyColumn {
                items(5) {
                    ArticleCardSkeleton(
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                    )
                }
            }
        }
        is ArticleListUiState.Success -> {
            ArticleList(articles = uiState.articles)
        }
        is ArticleListUiState.Error -> {
            // エラー表示
        }
    }
}
```

---

## 5. パフォーマンス最適化

### 5.1 不要なRecompositionの防止

```kotlin
// ✅ Stable/Immutableな型を使用
@Immutable
data class Article(
    val id: String,
    val title: String,
    val content: String
)

// ✅ ラムダをrememberでキャッシュ
@Composable
fun ArticleList(
    articles: List<Article>,
    viewModel: ArticleViewModel
) {
    val onArticleClick = remember<(Article) -> Unit> {
        { article -> viewModel.onArticleClick(article) }
    }

    LazyColumn {
        items(articles, key = { it.id }) { article ->
            ArticleCard(
                article = article,
                onClick = { onArticleClick(article) }
            )
        }
    }
}

// ✅ derivedStateOfで計算結果をキャッシュ
@Composable
fun FilteredList(items: List<Item>, filter: String) {
    val filteredItems by remember(items, filter) {
        derivedStateOf {
            items.filter { it.name.contains(filter, ignoreCase = true) }
        }
    }
    // ...
}
```

### 5.2 LazyListの最適化

```kotlin
@Composable
fun OptimizedLazyList(items: List<Item>) {
    LazyColumn(
        // ✅ 固定サイズの場合はcontentTypeを指定
        state = rememberLazyListState()
    ) {
        items(
            items = items,
            key = { it.id },  // ✅ 必ずkeyを指定
            contentType = { it.type }  // ✅ 異なる型のアイテムがある場合
        ) { item ->
            // ✅ 重い処理はrememberで最適化
            val processedData = remember(item) {
                heavyProcessing(item)
            }
            ItemCard(data = processedData)
        }
    }
}
```

### 5.3 画像の最適化

```kotlin
@Composable
fun OptimizedImage(
    imageUrl: String,
    modifier: Modifier = Modifier
) {
    AsyncImage(
        model = ImageRequest.Builder(LocalContext.current)
            .data(imageUrl)
            .crossfade(true)
            .memoryCachePolicy(CachePolicy.ENABLED)
            .diskCachePolicy(CachePolicy.ENABLED)
            .size(Size.ORIGINAL)  // または具体的なサイズ
            .build(),
        contentDescription = null,
        modifier = modifier,
        contentScale = ContentScale.Crop,
        placeholder = painterResource(R.drawable.placeholder),
        error = painterResource(R.drawable.error)
    )
}
```

---

## 6. アンチパターン

### 6.1 状態管理のアンチパターン

```kotlin
// ❌ Composable内でViewModelを生成
@Composable
fun BadScreen() {
    val viewModel = remember { MyViewModel() }  // NG: ライフサイクル問題
}

// ✅ Hiltなどで注入
@Composable
fun GoodScreen(
    viewModel: MyViewModel = hiltViewModel()
) { }

// ❌ 状態をprivateで隠蔽（テスト困難）
@Composable
fun BadComponent() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) {
        Text("$count")
    }
}

// ✅ 状態ホイスティング
@Composable
fun GoodComponent(
    count: Int,
    onIncrement: () -> Unit
) {
    Button(onClick = onIncrement) {
        Text("$count")
    }
}
```

### 6.2 パフォーマンスのアンチパターン

```kotlin
// ❌ Composable内で重い処理
@Composable
fun BadList(items: List<Item>) {
    val sorted = items.sortedBy { it.name }  // 毎回ソート
    LazyColumn {
        items(sorted) { /* ... */ }
    }
}

// ✅ rememberでキャッシュ
@Composable
fun GoodList(items: List<Item>) {
    val sorted = remember(items) { items.sortedBy { it.name } }
    LazyColumn {
        items(sorted, key = { it.id }) { /* ... */ }
    }
}

// ❌ インラインラムダ（毎回新しいインスタンス）
@Composable
fun BadItem(item: Item, viewModel: ViewModel) {
    Button(onClick = { viewModel.onClick(item) }) {  // 毎回再生成
        Text(item.name)
    }
}

// ✅ rememberでラムダをキャッシュ
@Composable
fun GoodItem(item: Item, onClick: () -> Unit) {
    Button(onClick = onClick) {
        Text(item.name)
    }
}

// ❌ LazyColumnでkeyなし
LazyColumn {
    items(articles) { article ->  // keyがないとパフォーマンス低下
        ArticleCard(article)
    }
}

// ✅ keyを指定
LazyColumn {
    items(articles, key = { it.id }) { article ->
        ArticleCard(article)
    }
}
```

### 6.3 レイアウトのアンチパターン

```kotlin
// ❌ 不必要なネスト
@Composable
fun BadLayout() {
    Box {
        Box {
            Column {
                Row {
                    Text("Hello")
                }
            }
        }
    }
}

// ✅ シンプルな構造
@Composable
fun GoodLayout() {
    Text("Hello")
}

// ❌ fillMaxSizeの乱用
@Composable
fun BadSizing() {
    Column(modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier.fillMaxSize()) {  // 問題: 全画面を占有
            Text("Content")
        }
    }
}

// ✅ 適切なサイズ指定
@Composable
fun GoodSizing() {
    Column(modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier.weight(1f)) {
            Text("Content")
        }
    }
}
```

### 6.4 Side Effectのアンチパターン

```kotlin
// ❌ Composable内で直接副作用
@Composable
fun BadEffect(viewModel: ViewModel) {
    viewModel.trackScreen()  // Recomposition毎に実行される
}

// ✅ LaunchedEffectを使用
@Composable
fun GoodEffect(viewModel: ViewModel) {
    LaunchedEffect(Unit) {
        viewModel.trackScreen()
    }
}

// ❌ remember内で副作用
@Composable
fun BadRemember() {
    val data = remember {
        fetchData()  // 副作用をremember内で実行
    }
}

// ✅ LaunchedEffectで非同期処理
@Composable
fun GoodAsync(viewModel: ViewModel) {
    val data by viewModel.data.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.fetchData()
    }
}
```

### 6.5 テスタビリティのアンチパターン

```kotlin
// ❌ ハードコードされた依存関係
@Composable
fun BadScreen() {
    val context = LocalContext.current
    val repository = RealRepository(context)  // テスト困難
    // ...
}

// ✅ 依存性注入
@Composable
fun GoodScreen(
    viewModel: ScreenViewModel = hiltViewModel()
) {
    // ViewModelに依存関係を注入
}

// ❌ プレビューできないComposable
@Composable
fun BadPreview() {
    val viewModel: RealViewModel = hiltViewModel()  // プレビュー不可
    Content(viewModel.uiState)
}

// ✅ プレビュー可能な設計
@Composable
fun GoodContent(uiState: UiState) {
    // 状態のみに依存
}

@Preview
@Composable
private fun ContentPreview() {
    GoodContent(
        uiState = UiState.Success(sampleData)
    )
}
```

---

## 7. テスタビリティ

### 7.1 テスト可能な設計

```kotlin
// ✅ UIロジックを分離
class FormValidator {
    fun validateEmail(email: String): ValidationResult {
        return when {
            email.isBlank() -> ValidationResult.Error("メールアドレスを入力してください")
            !email.contains("@") -> ValidationResult.Error("正しいメールアドレスを入力してください")
            else -> ValidationResult.Valid
        }
    }
}

// ✅ プレビュー用のサンプルデータ
object PreviewData {
    val sampleArticle = Article(
        id = "1",
        title = "サンプル記事",
        content = "これはサンプルです"
    )

    val sampleArticleList = listOf(
        sampleArticle,
        sampleArticle.copy(id = "2", title = "記事2")
    )
}

@Preview
@Composable
private fun ArticleCardPreview() {
    MaterialTheme {
        ArticleCard(
            article = PreviewData.sampleArticle,
            onClick = {}
        )
    }
}
```

### 7.2 Compose UIテスト

```kotlin
class ArticleCardTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun articleCard_displaysTitle() {
        val article = Article(
            id = "1",
            title = "テスト記事",
            content = "内容"
        )

        composeTestRule.setContent {
            ArticleCard(
                article = article,
                onClick = {}
            )
        }

        composeTestRule
            .onNodeWithText("テスト記事")
            .assertIsDisplayed()
    }

    @Test
    fun articleCard_clickTriggersCallback() {
        var clicked = false

        composeTestRule.setContent {
            ArticleCard(
                article = PreviewData.sampleArticle,
                onClick = { clicked = true }
            )
        }

        composeTestRule
            .onNodeWithText(PreviewData.sampleArticle.title)
            .performClick()

        assertTrue(clicked)
    }
}
```

---

## 8. チェックリスト

### 実装前チェック
- [ ] 再利用可能なコンポーネントか確認
- [ ] 状態ホイスティングを適用できるか確認
- [ ] Modifierパラメータを追加したか

### 実装中チェック
- [ ] keyをLazyListに指定したか
- [ ] 重い処理をrememberでキャッシュしたか
- [ ] 副作用をLaunchedEffect等で適切に処理しているか

### 実装後チェック
- [ ] @Previewが動作するか
- [ ] 不要なRecompositionがないか（Layout Inspectorで確認）
- [ ] テストコードを書いたか
