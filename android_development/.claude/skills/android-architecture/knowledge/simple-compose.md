# シンプルCompose パターンガイド

展示会デモやモックアプリ向けの、ViewModelを使わないシンプルなCompose実装パターンです。

---

## 1. シンプルComposeとは

### 1.1 概要

ViewModelやMVI/MVVMなどのアーキテクチャパターンを使用せず、**Compose内で直接状態を管理**するアプローチです。

```
MainActivity
    │
    ▼
AppNavigation (remember + mutableStateOf)
    │
    ▼
Screen Composables
```

### 1.2 他パターンとの比較

| 観点 | シンプルCompose | MVVM | MVI |
|------|-----------------|------|-----|
| 学習コスト | 最低 | 低 | 中〜高 |
| ボイラープレート | 最小 | 少 | 多 |
| テスタビリティ | 低 | 中 | 高 |
| 状態追跡 | 困難 | 可能 | 容易 |
| 適用規模 | 小〜中 | 中 | 中〜大 |

### 1.3 シンプルComposeを選ぶべき場面

**推奨**:
- 展示会デモ/モックアプリ
- プロトタイプ開発
- 状態が画面内で完結
- 短期間での実装が必要
- 長期メンテナンス予定なし

**非推奨**:
- 本番リリース予定のアプリ
- 複数画面で状態を共有
- テストカバレッジが必要
- チーム開発で一貫性が重要

---

## 2. 基本構造

### 2.1 プロジェクト構成

```
app/
└── src/main/java/com/example/app/
    ├── MainActivity.kt           # エントリポイント
    ├── ui/
    │   ├── navigation/
    │   │   └── AppNavigation.kt  # ナビゲーション + 状態管理
    │   ├── screens/              # 各画面
    │   │   ├── HomeScreen.kt
    │   │   ├── DetailScreen.kt
    │   │   └── SettingScreen.kt
    │   ├── components/           # 共通コンポーネント
    │   │   ├── CommonButton.kt
    │   │   └── LoadingIndicator.kt
    │   ├── model/                # データモデル
    │   │   └── AppData.kt
    │   └── theme/                # テーマ
    │       └── Theme.kt
    └── utils/                    # ユーティリティ
```

### 2.2 シングルモジュール

domain/data層の分離は不要。すべてをappモジュールに配置。

---

## 3. 実装パターン

### 3.1 MainActivity

```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            AppTheme {
                AppNavigation()
            }
        }
    }
}
```

### 3.2 AppNavigation（状態管理の中心）

```kotlin
@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    // アプリ全体の状態をここで管理
    var selectedItem by remember { mutableStateOf<Item?>(null) }
    var isLoading by remember { mutableStateOf(false) }

    NavHost(
        navController = navController,
        startDestination = "home"
    ) {
        composable("home") {
            HomeScreen(
                onItemClick = { item ->
                    selectedItem = item
                    navController.navigate("detail")
                }
            )
        }

        composable("detail") {
            DetailScreen(
                item = selectedItem,
                onBack = { navController.popBackStack() }
            )
        }

        composable("settings") {
            SettingScreen(
                onBack = { navController.popBackStack() }
            )
        }
    }
}
```

### 3.3 Screen Composable

```kotlin
@Composable
fun HomeScreen(
    onItemClick: (Item) -> Unit,
) {
    // 画面内の状態
    var searchQuery by remember { mutableStateOf("") }
    val items = remember { getSampleItems() }  // ハードコードデータ

    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        // 検索バー
        TextField(
            value = searchQuery,
            onValueChange = { searchQuery = it },
            placeholder = { Text("Search...") },
            modifier = Modifier.fillMaxWidth()
        )

        // リスト表示
        LazyColumn {
            items(
                items.filter { it.name.contains(searchQuery, ignoreCase = true) }
            ) { item ->
                ItemCard(
                    item = item,
                    onClick = { onItemClick(item) }
                )
            }
        }
    }
}
```

---

## 4. 状態管理のパターン

### 4.1 remember + mutableStateOf

最もシンプルな状態管理。

```kotlin
@Composable
fun CounterScreen() {
    var count by remember { mutableStateOf(0) }

    Column {
        Text("Count: $count")
        Button(onClick = { count++ }) {
            Text("Increment")
        }
    }
}
```

### 4.2 rememberSaveable（画面回転対応）

```kotlin
@Composable
fun FormScreen() {
    var name by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }

    Column {
        TextField(value = name, onValueChange = { name = it })
        TextField(value = email, onValueChange = { email = it })
    }
}
```

### 4.3 複数状態の管理

```kotlin
// data class で状態をまとめる
data class FormState(
    val name: String = "",
    val email: String = "",
    val isSubmitting: Boolean = false,
)

@Composable
fun FormScreen() {
    var state by remember { mutableStateOf(FormState()) }

    Column {
        TextField(
            value = state.name,
            onValueChange = { state = state.copy(name = it) }
        )
        TextField(
            value = state.email,
            onValueChange = { state = state.copy(email = it) }
        )

        if (state.isSubmitting) {
            CircularProgressIndicator()
        }
    }
}
```

---

## 5. ナビゲーションパターン

### 5.1 Screen定義（sealed class）

```kotlin
sealed class Screen(val route: String) {
    object Home : Screen("home")
    object Detail : Screen("detail/{id}") {
        fun createRoute(id: String) = "detail/$id"
    }
    object Settings : Screen("settings")
}
```

### 5.2 パラメータ付きナビゲーション

```kotlin
NavHost(
    navController = navController,
    startDestination = Screen.Home.route
) {
    composable(Screen.Home.route) {
        HomeScreen(
            onItemClick = { id ->
                navController.navigate(Screen.Detail.createRoute(id))
            }
        )
    }

    composable(
        route = Screen.Detail.route,
        arguments = listOf(navArgument("id") { type = NavType.StringType })
    ) { backStackEntry ->
        val id = backStackEntry.arguments?.getString("id") ?: ""
        DetailScreen(
            itemId = id,
            onBack = { navController.popBackStack() }
        )
    }
}
```

---

## 6. データの扱い

### 6.1 ハードコードデータ

展示会デモではAPIは不要。データはコード内に直接記述。

```kotlin
// model/SampleData.kt
object SampleData {
    val items = listOf(
        Item(
            id = "1",
            name = "サンプル商品1",
            price = 1000,
            imageRes = R.drawable.item1
        ),
        Item(
            id = "2",
            name = "サンプル商品2",
            price = 2000,
            imageRes = R.drawable.item2
        ),
    )
}

// 使用側
@Composable
fun ItemListScreen() {
    val items = remember { SampleData.items }
    // ...
}
```

### 6.2 リソースファイルの活用

多言語対応やデータ変更を想定する場合はstrings.xmlを活用。

```xml
<!-- strings.xml -->
<resources>
    <string name="item_1_name">サンプル商品1</string>
    <string name="item_1_description">商品の説明文...</string>
</resources>
```

```kotlin
data class Item(
    val id: String,
    val nameResId: Int,
    val descriptionResId: Int,
)
```

---

## 7. 展示会向け機能

### 7.1 Kioskモード

```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // フルスクリーン
        enableEdgeToEdge()
        hideSystemUI()

        setContent {
            AppTheme {
                AppNavigation()
            }
        }
    }

    private fun hideSystemUI() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            window.insetsController?.let { controller ->
                controller.hide(WindowInsets.Type.systemBars())
                controller.systemBarsBehavior =
                    WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            }
        }
    }
}
```

### 7.2 アイドルタイマー

```kotlin
class IdleTimerManager(
    private val timeoutMillis: Long = 60_000L,  // 1分
    private val onTimeout: () -> Unit,
) {
    private var job: Job? = null

    fun start(scope: CoroutineScope) {
        job?.cancel()
        job = scope.launch {
            delay(timeoutMillis)
            onTimeout()
        }
    }

    fun reset(scope: CoroutineScope) {
        start(scope)  // タイマーをリセット
    }

    fun stop() {
        job?.cancel()
    }
}

// 使用例
@Composable
fun AppNavigation() {
    val scope = rememberCoroutineScope()
    val navController = rememberNavController()

    val idleTimer = remember {
        IdleTimerManager(
            timeoutMillis = 60_000L,
            onTimeout = {
                // ホーム画面に戻る
                navController.popBackStack(Screen.Home.route, inclusive = false)
            }
        )
    }

    // 各画面でユーザー操作時にresetを呼ぶ
}
```

### 7.3 シナリオベースのデモ

```kotlin
enum class DemoScenario {
    SCENARIO_A,
    SCENARIO_B,
    SCENARIO_C,
}

@Composable
fun AppNavigation() {
    // 起動時にランダム選択
    val scenario = remember { DemoScenario.values().random() }

    val items = remember {
        when (scenario) {
            DemoScenario.SCENARIO_A -> ScenarioAData.items
            DemoScenario.SCENARIO_B -> ScenarioBData.items
            DemoScenario.SCENARIO_C -> ScenarioCData.items
        }
    }

    // ...
}
```

---

## 8. 注意点

### 8.1 状態の巻き上げ（State Hoisting）

親Composableで状態を管理し、子には状態とコールバックを渡す。

```kotlin
// OK: 状態を親で管理
@Composable
fun ParentScreen() {
    var text by remember { mutableStateOf("") }

    ChildComponent(
        text = text,
        onTextChange = { text = it }
    )
}

@Composable
fun ChildComponent(
    text: String,
    onTextChange: (String) -> Unit,
) {
    TextField(value = text, onValueChange = onTextChange)
}
```

### 8.2 再コンポジションの最適化

頻繁に更新される状態は、影響範囲を限定する。

```kotlin
// NG: 全体が再コンポジションされる
@Composable
fun BadExample() {
    var counter by remember { mutableStateOf(0) }

    Column {
        Text("Counter: $counter")
        ExpensiveComponent()  // これも再コンポジションされる
        Button(onClick = { counter++ }) { Text("Increment") }
    }
}

// OK: 状態を使う部分だけ分離
@Composable
fun GoodExample() {
    Column {
        CounterSection()
        ExpensiveComponent()  // 影響を受けない
    }
}

@Composable
private fun CounterSection() {
    var counter by remember { mutableStateOf(0) }
    Text("Counter: $counter")
    Button(onClick = { counter++ }) { Text("Increment") }
}
```

---

## 9. 本番化する場合

シンプルComposeで作ったモックを本番化する場合の移行手順。

### 9.1 段階的な移行

1. **ViewModelの導入**
   - 画面ごとにViewModelを作成
   - `remember { mutableStateOf }` → `viewModel.uiState` に移行

2. **Repository層の追加**
   - ハードコードデータ → Repository経由に
   - API/DBの接続

3. **DI（Hilt）の導入**
   - ViewModelへの依存注入
   - Repositoryの注入

4. **テストの追加**
   - ViewModelテスト
   - 結合テスト

### 9.2 移行しない判断

以下の場合は移行不要:
- 展示会終了後に破棄
- 別途本番アプリを新規開発
- モックとしての役割を継続

---

## 10. 参考資料

- [AI HOME実装例](./aihome-example.md) - 展示会デモの実例
- [MVVMパターン](./mvvm-pattern.md) - 本番化時の移行先
- [Jetpack Compose State](https://developer.android.com/jetpack/compose/state)

---

**作成日**: 2026-01-13
**作成者**: Claude Code（android-architectureスキル）
