# 既存プロジェクトへのMVI移行ガイド

既存のMVVMやMVPプロジェクトからMVIへ段階的に移行するためのガイドです。

---

## 1. 移行の判断基準

### 1.1 移行すべきケース

| 状況 | 移行推奨度 |
|------|-----------|
| 状態管理のバグが頻発 | ★★★ 強く推奨 |
| 複数の非同期処理が絡む画面がある | ★★★ 強く推奨 |
| チームが拡大予定 | ★★☆ 推奨 |
| テストカバレッジを上げたい | ★★☆ 推奨 |
| 既存コードが安定している | ★☆☆ 慎重に検討 |

### 1.2 移行しないほうが良いケース

- プロジェクト終了間近
- チームにMVI経験者がいない＆学習時間がない
- 既存アーキテクチャで問題が発生していない

---

## 2. 移行戦略

### 2.1 Big Bang vs 段階的移行

| 戦略 | メリット | デメリット |
|------|---------|-----------|
| **Big Bang** | 一貫性が保てる | リスク大、工数大 |
| **段階的移行** | リスク分散、学習しながら進める | 一時的に混在状態 |

**推奨: 段階的移行**

### 2.2 段階的移行のステップ

```
Phase 1: 基盤クラス導入（1-2日）
    ↓
Phase 2: 新規画面でMVI採用（画面ごと）
    ↓
Phase 3: 複雑な既存画面をMVIに移行（優先度順）
    ↓
Phase 4: 残りの画面を移行（余裕があれば）
```

---

## 3. Phase 1: 基盤クラス導入

### 3.1 ディレクトリ構造

```
ui/
└── common/
    └── mvi/
        ├── MviIntent.kt
        ├── MviAction.kt
        ├── MviState.kt
        ├── MviEvent.kt
        ├── StateManager.kt
        ├── StateReducer.kt
        └── MviPresenter.kt
```

### 3.2 基盤インターフェース

```kotlin
// MviIntent.kt
interface MviIntent

// MviAction.kt
interface MviAction

// MviState.kt
interface MviState

// MviEvent.kt
interface MviEvent
```

### 3.3 StateManager基底クラス

```kotlin
// StateManager.kt
abstract class StateManager<
    I : MviIntent,
    A : MviAction,
    S : MviState,
    E : MviEvent
>(
    protected val coroutineScope: CoroutineScope,
    initialState: S,
) {
    protected val _state = MutableStateFlow(initialState)
    val state: StateFlow<S> = _state.asStateFlow()

    protected val _events = MutableSharedFlow<E>(replay = 0)
    val events: SharedFlow<E> = _events.asSharedFlow()

    abstract fun processIntent(intent: I): List<A>

    abstract suspend fun handleAction(action: A)

    protected fun updateState(newState: S) {
        _state.value = newState
    }

    protected suspend fun emitEvent(event: E) {
        _events.emit(event)
    }
}
```

### 3.4 StateReducer基底クラス

```kotlin
// StateReducer.kt
abstract class StateReducer<S : MviState, A : MviAction> {
    abstract fun reduce(currentState: S, action: A): S
}
```

---

## 4. Phase 2: 新規画面でMVI採用

### 4.1 対象画面の選定

**良い候補**:
- 新規追加の画面
- 複雑な状態管理が予想される画面
- チームの学習教材として適した画面

**避けるべき**:
- 既存コードとの依存が強い画面
- 緊急リリースが必要な画面

### 4.2 実装チェックリスト

```markdown
## 新規MVI画面チェックリスト

### 定義ファイル
- [ ] [Feature]Intent.kt - ユーザー操作の定義
- [ ] [Feature]Action.kt - 内部アクションの定義
- [ ] [Feature]UiState.kt - 画面状態の定義
- [ ] [Feature]UiEvent.kt - 一回限りイベントの定義

### MVIコンポーネント
- [ ] [Feature]Reducer.kt - 純粋な状態変換
- [ ] [Feature]Presenter.kt - 副作用処理
- [ ] [Feature]StateManager.kt - フロー制御

### Android統合
- [ ] [Feature]ViewModel.kt - ライフサイクル管理
- [ ] [Feature]Screen.kt - Compose UI

### DI
- [ ] [Feature]MviModule.kt - Hilt Module

### テスト
- [ ] [Feature]ReducerTest.kt - Reducer単体テスト
```

---

## 5. Phase 3: 既存画面のMVI移行

### 5.1 優先度の決め方

| 優先度 | 条件 |
|--------|------|
| 高 | バグが多い、状態管理が複雑 |
| 中 | 改修予定がある、テストを書きたい |
| 低 | 安定している、改修予定なし |

### 5.2 MVVMからMVIへの変換パターン

#### Before: MVVM

```kotlin
@HiltViewModel
class ArticleViewModel @Inject constructor(
    private val repository: ArticleRepository,
) : ViewModel() {

    private val _articles = MutableStateFlow<List<Article>>(emptyList())
    val articles: StateFlow<List<Article>> = _articles.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    fun loadArticles() {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null
            repository.getArticles()
                .onSuccess { _articles.value = it }
                .onFailure { _error.value = it.message }
            _isLoading.value = false
        }
    }
}
```

#### After: MVI

```kotlin
// 1. State統合
@Immutable
sealed interface ArticleUiState : MviState {
    data object Loading : ArticleUiState
    data class Success(val articles: ImmutableList<Article>) : ArticleUiState
    data class Error(val message: String) : ArticleUiState
}

// 2. Intent定義
sealed interface ArticleIntent : MviIntent {
    data object LoadArticles : ArticleIntent
}

// 3. ViewModel簡素化
@HiltViewModel
class ArticleViewModel @Inject constructor(
    private val stateManager: ArticleStateManager,
) : ViewModel() {
    val uiState: StateFlow<ArticleUiState> = stateManager.state

    fun onIntent(intent: ArticleIntent) {
        viewModelScope.launch {
            stateManager.processIntent(intent).forEach {
                stateManager.handleAction(it)
            }
        }
    }
}
```

### 5.3 段階的移行のコツ

1. **まずStateを統合**
   - 複数のStateFlowを1つのsealed interfaceに

2. **次にIntentを定義**
   - 既存のpublic関数をIntentに置き換え

3. **Reducerを抽出**
   - 状態変更ロジックを純粋関数に

4. **Presenterを分離**
   - 副作用処理を分離

5. **StateManagerで統合**
   - フロー制御を一元化

---

## 6. 共存パターン

### 6.1 MVVMとMVIの共存

移行期間中は両パターンが共存します。

```
ui/
├── common/
│   └── mvi/           # MVI基盤
├── feature/
│   ├── article/       # MVI採用
│   │   ├── ArticleScreen.kt
│   │   ├── ArticleViewModel.kt  # MVI
│   │   └── mvi/
│   └── setting/       # MVVM維持
│       ├── SettingScreen.kt
│       └── SettingViewModel.kt  # MVVM
```

### 6.2 命名規則での区別

```kotlin
// MVI画面
class ArticleViewModel      // StateManagerを使用
class ArticleStateManager
class ArticleReducer

// MVVM画面（既存）
class SettingViewModel      // 従来のMVVM
```

---

## 7. トラブルシューティング

### 7.1 よくある問題

**問題1: 状態の不整合**

```kotlin
// NG: 複数箇所で状態を更新
_state.value = _state.value.copy(isLoading = true)
// ... 別の場所で
_state.value = _state.value.copy(articles = newArticles)
// isLoadingが消えてしまう可能性
```

```kotlin
// OK: Reducerで一元管理
fun reduce(state: State, action: Action): State = when (action) {
    is ShowLoading -> state.copy(isLoading = true)
    is UpdateArticles -> state.copy(
        isLoading = false,
        articles = action.articles
    )
}
```

**問題2: Eventの二重発火**

```kotlin
// NG: replay = 1だと再購読時に再発火
private val _events = MutableSharedFlow<E>(replay = 1)

// OK: replay = 0で一回限り
private val _events = MutableSharedFlow<E>(replay = 0)
```

**問題3: 循環参照**

```kotlin
// NG: StateManagerとPresenterが相互参照
class StateManager(private val presenter: Presenter)
class Presenter(private val stateManager: StateManager)  // 循環!

// OK: Presenterは状態を持たない
class Presenter(private val useCase: UseCase)  // UseCaseのみ依存
```

### 7.2 デバッグTips

```kotlin
// 状態変化のログ出力
class ArticleStateManager(...) : StateManager<...>(...) {
    override suspend fun handleAction(action: ArticleAction) {
        Log.d("MVI", "Action: $action")
        Log.d("MVI", "State Before: ${_state.value}")

        // ... 処理 ...

        Log.d("MVI", "State After: ${_state.value}")
    }
}
```

---

## 8. 移行完了の判断基準

### 8.1 チェックリスト

```markdown
## 移行完了チェックリスト

### 技術的観点
- [ ] 全画面でMVI or 意図的なMVVM維持
- [ ] 基盤クラスが安定
- [ ] Reducerのテストカバレッジ80%以上

### チーム観点
- [ ] 全メンバーがMVIを理解
- [ ] コードレビューでMVI観点のチェック可能
- [ ] 新規画面はMVIで実装する合意

### 品質観点
- [ ] 状態管理関連のバグが減少
- [ ] デバッグ時間が短縮
```

### 8.2 成功指標

| 指標 | 移行前 | 移行後目標 |
|------|--------|-----------|
| 状態管理バグ数/月 | X件 | 50%減 |
| 新機能実装時間 | Xh | 20%減 |
| Reducerテストカバレッジ | 0% | 80%+ |

---

## 9. 参考資料

- [MVIパターン詳細](./mvi-pattern.md)
- [dmenunews実装例](./dmenunews-example.md)
- [Android Architecture Components](https://developer.android.com/topic/architecture)
