# AI HOME (docomo-home-ui-mock) アーキテクチャガイド

MWC2026展示会向けのUIモックアプリケーションのアーキテクチャ設計と実装パターンについて解説します。

---

## 1. プロジェクト概要

### 1.1 プロジェクトの特徴

| 項目 | 内容 |
|------|------|
| **用途** | MWC2026展示会向けUIモックアプリ |
| **特徴** | キオスクモード、シナリオベースのデモ |
| **アーキテクチャ** | シンプルなCompose UI（MVI/MVVMなし） |
| **モジュール構成** | シングルモジュール |

### 1.2 ディレクトリ構造

```
docomo-home-ui-mock/
├── app/
│   └── src/main/java/com/docomo/homemock/
│       ├── MainActivity.kt           # アプリエントリポイント、Kioskモード管理
│       ├── KioskDeviceAdminReceiver.kt  # Device Owner用レシーバー
│       ├── ui/
│       │   ├── navigation/
│       │   │   └── AppNavigation.kt  # ナビゲーション + レイヤー管理
│       │   ├── screens/              # 各画面のComposable（40+ファイル）
│       │   ├── components/           # 共通コンポーネント
│       │   ├── model/                # データモデル（AppInfo, StoryConfig）
│       │   ├── theme/                # テーマ設定
│       │   └── gesture/              # ジェスチャーハンドラー
│       └── utils/
│           └── IdleTimerManager.kt   # アイドルタイマー管理
└── docs/                             # ドキュメント
```

---

## 2. 設計思想

### 2.1 シンプルなアーキテクチャを選択した理由

| 観点 | 理由 |
|------|------|
| **用途特化** | 展示会デモ用モックのため、本番アプリほどの堅牢性不要 |
| **状態管理** | 画面間で共有する状態が少ない（シナリオ選択程度） |
| **開発速度** | 短期間で多数の画面を実装する必要があった |
| **メンテナンス** | 展示会後の長期メンテナンス予定なし |

### 2.2 アーキテクチャの特徴

```
┌─────────────────────────────────────────────────────────────┐
│                      MainActivity                           │
│   ・Kioskモード管理                                         │
│   ・システムUI制御                                          │
│   ・ライフサイクル管理                                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     AppNavigation                           │
│   ・NavHost によるルーティング                              │
│   ・レイヤーベースのアニメーション管理                      │
│   ・シナリオ状態管理（remember + mutableStateOf）           │
│   ・IdleTimerManager との連携                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Screen Composables                       │
│   ・各画面のUI定義（40+画面）                               │
│   ・画像ベースのモック画面（ImageBasedAppScreen）          │
│   ・コールバックでナビゲーション操作                        │
└─────────────────────────────────────────────────────────────┘
```

**MVVMやMVIを採用していない**:
- ViewModelなし（画面状態はComposable内でrememberで管理）
- Repositoryなし（データはハードコード）
- UseCaseなし（ビジネスロジックなし）

---

## 3. ナビゲーション設計

### 3.1 Screen定義

```kotlin
sealed class Screen(val route: String) {
    object Lock : Screen("lock")
    object AppCards : Screen("app_cards")
    object CalendarApp : Screen("calendar_app")
    object WeatherApp : Screen("weather_app")
    // ... 40+画面

    // パラメータ付きルート
    object AiChatApp : Screen("chat/{context}") {
        fun createRoute(context: String = "GENERIC") = "chat/$context"
    }
}
```

### 3.2 レイヤーベースのアニメーション

**特殊な実装パターン**: NavControllerではなくレイヤー管理で画面遷移を実現

```kotlin
// AppNavigation.kt内のレイヤー管理
Box(modifier = Modifier.fillMaxSize()) {
    // Layer 0: Home Screen (background, scaled)
    HomeScreen(
        modifier = Modifier.graphicsLayer {
            scaleX = homeScale.value  // 0.90 ↔ 1.0
            scaleY = homeScale.value
        },
        ...
    )

    // Layer 1: App Card Screen (foreground, fades)
    if (appCardsAlpha.value > 0f) {
        AppCardScreen(
            modifier = Modifier.graphicsLayer {
                alpha = appCardsAlpha.value  // 0.0 ↔ 1.0
            },
            ...
        )
    }

    // Layer 2: Full Screen App Overlay
    currentFullScreenApp?.let { route ->
        FullScreenAppOverlay(...)
    }
}
```

**この設計の理由**:
- Recent Apps風のスワイプアニメーション実現
- ちらつき防止（常時レンダリング方式）
- 複雑なトランジションをNavControllerに依存せず制御

---

## 4. 状態管理

### 4.1 Composable内での状態管理

```kotlin
@Composable
fun AppNavigation(onExitKiosk: () -> Unit = {}) {
    val navController = rememberNavController()
    val scope = rememberCoroutineScope()

    // シナリオ状態（アプリ起動時にランダム選択）
    val initialScenario = remember { listOf(1, 2, 3).random() }
    var currentScenario by remember { mutableStateOf(initialScenario) }

    // 選択されたアプリリスト
    var selectedApps by remember { mutableStateOf(getAppsForScenario(initialScenario)) }

    // アニメーション状態
    val appCardsAlpha = remember { Animatable(1f) }
    val homeScale = remember { Animatable(0.90f) }

    // ...
}
```

### 4.2 シナリオ管理

```kotlin
// 3つのUXシナリオ
enum class UxStory {
    TRAINING,   // UX1: トレーニング
    TRAVEL,     // UX2: 旅行
    SOCCER      // UX3: サッカー
}

// シナリオ設定
data class StoryConfig(
    val story: UxStory,
    val wallpaperRes: Int,
    val calloutType: CalloutType,
    val greetingMessageResId: Int,
    val apps: List<AppInfo>
)
```

---

## 5. Kioskモード実装

### 5.1 MainActivity での設定

```kotlin
class MainActivity : ComponentActivity() {
    private fun setupKioskMode() {
        // ロック画面バイパス
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O_MR1) {
            setShowWhenLocked(true)
            setTurnScreenOn(true)
            keyguardManager.requestDismissKeyguard(this, null)
        }

        // Device Owner設定
        setupDeviceOwnerLockTask()

        // Lock Task開始
        startLockTask()
    }

    private fun setupDeviceOwnerLockTask() {
        val dpm = getSystemService(DEVICE_POLICY_SERVICE) as DevicePolicyManager
        if (dpm.isDeviceOwnerApp(packageName)) {
            dpm.setLockTaskPackages(componentName, arrayOf(packageName))
            dpm.setLockTaskFeatures(componentName, LOCK_TASK_FEATURE_NONE)
        }
    }
}
```

### 5.2 システムUI制御

```kotlin
private fun hideSystemUI() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        window.insetsController?.let { controller ->
            controller.systemBarsBehavior = BEHAVIOR_DEFAULT
            controller.hide(WindowInsets.Type.systemBars())
        }
    }
    excludeSystemGestures()  // ジェスチャー無効化
}
```

---

## 6. データモデル

### 6.1 AppInfo（アプリ情報）

```kotlin
data class AppInfo(
    val id: String,
    val cardTitleResId: Int,
    val screenTitleResId: Int,
    val backgroundColor: Color,
    val aiMessageResId: Int,
    val notificationTitleResId: Int,
    val notificationBodyResId: Int,
    val navigationRoute: String,
    val actionButtons: List<ActionButton> = emptyList()
)

// 使用例
val ALL_APPS: List<AppInfo> = listOf(
    AppInfo(
        id = "training",
        cardTitleResId = R.string.card_title_training,
        navigationRoute = "training_app",
        actionButtons = listOf(
            ActionButton(R.string.button_watch_video, "video_app", COLOR_GREEN),
            ActionButton(R.string.button_ask_ai, "chat/GENERIC", COLOR_ORANGE)
        )
    ),
    // ...
)
```

### 6.2 ActionButton（ボタン定義）

```kotlin
data class ActionButton(
    val textResId: Int,
    val route: String,
    val color: Color,
    val iconImageVector: ImageVector = Icons.Default.PlayArrow
)
```

---

## 7. 画面実装パターン

### 7.1 ImageBasedAppScreen（画像ベース画面）

多くの画面は静的な画像を表示するパターンで実装：

```kotlin
@Composable
fun TrainingAppScreen(
    onBack: () -> Unit,
    onUserInteraction: () -> Unit,
    overlayMode: Boolean = false  // フルスクリーンオーバーレイ時はtrue
) {
    ImageBasedAppScreen(
        imageRes = R.drawable.screen_training,
        onBack = onBack,
        onUserInteraction = onUserInteraction,
        overlayMode = overlayMode
    )
}
```

### 7.2 IdleTimer連携

```kotlin
composable(Screen.CalendarApp.route) {
    LaunchedEffect(Unit) {
        idleTimerManager.start()
    }

    CalendarAppScreen(
        onBack = { safeNavigateBack(navController) },
        onUserInteraction = { idleTimerManager.resetTimer() }
    )
}
```

---

## 8. dmenunewsとの比較

| 観点 | AI HOME | dmenunews |
|------|---------|-----------|
| **用途** | 展示会デモ | 本番アプリ |
| **モジュール** | シングル | マルチ（app/ui/domain/data） |
| **アーキテクチャ** | なし（Compose直接） | Clean Architecture + MVI |
| **状態管理** | remember + mutableStateOf | StateFlow + StateManager |
| **データ** | ハードコード | Room + Retrofit |
| **DI** | なし | Hilt |
| **テスト** | なし | Reducer/UseCase単体テスト |

### 8.1 AI HOMEにMVIを導入すべきか？

**結論: 不要**

理由:
- 展示会終了後の長期メンテナンス予定なし
- 状態管理の複雑さが低い
- 現在の実装で十分な品質を達成

ただし、**本番アプリ化する場合**は以下を検討：
1. モジュール分割（ui/domain/data）
2. MVI導入（複雑な状態管理対応）
3. DI導入（テスタビリティ向上）
4. Repository層追加（データソース抽象化）

---

## 9. 開発Tips

### 9.1 新しい画面を追加する手順

1. **Screen定義を追加**
```kotlin
// AppNavigation.kt
object NewApp : Screen("new_app")
```

2. **Composableを作成**
```kotlin
// screens/NewAppScreen.kt
@Composable
fun NewAppScreen(
    onBack: () -> Unit,
    onUserInteraction: () -> Unit,
    overlayMode: Boolean = false
) {
    // 実装
}
```

3. **NavHostに登録**
```kotlin
composable(Screen.NewApp.route) {
    LaunchedEffect(Unit) { idleTimerManager.start() }
    NewAppScreen(
        onBack = { safeNavigateBack(navController) },
        onUserInteraction = { idleTimerManager.resetTimer() }
    )
}
```

4. **フルスクリーンオーバーレイに追加（必要な場合）**
```kotlin
// FullScreenAppOverlay内
Screen.NewApp.route -> NewAppScreen(
    onBack = onClose,
    onUserInteraction = onUserInteraction,
    overlayMode = true
)
```

### 9.2 シナリオにアプリを追加

```kotlin
// AppInfo.kt
val ALL_APPS: List<AppInfo> = listOf(
    // 既存アプリ...
    AppInfo(
        id = "new_app",
        cardTitleResId = R.string.card_title_new_app,
        navigationRoute = "new_app",
        // ...
    )
)
```

---

## 10. 参考リソース

- [Jetpack Compose Navigation](https://developer.android.com/jetpack/compose/navigation)
- [Device Owner Mode](https://developer.android.com/work/dpc/dedicated-devices)
- [dmenunews実装例](./dmenunews-example.md) - 本番アプリのアーキテクチャ参考

---

**作成日**: 2026-01-13
**作成者**: Claude Code（android-architectureスキル）
**計測時間**: 約5分（プロジェクト分析〜ドキュメント生成）
