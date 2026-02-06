# プロジェクト設定テンプレート

このファイルをプロジェクトの `.claude/skills/android-test-generator/knowledge/` にコピーし、プロジェクト固有の設定を記述してください。

---

## 基本設定

```yaml
# プロジェクト名
project_name: "your-project-name"

# テスト対象パッケージ
test_package: "com.example.app"

# テストディレクトリ
test_directory: "app/src/test/java"
```

---

## モジュール別設定

各モジュール（層）ごとにテスト設定を定義する。テスト対象クラスの属するモジュールに応じて設定が自動適用される。

### Domain 層（UseCase / DomainModel）

```yaml
domain:
  assertion: "junit"              # JUnit Assert が主力
  coroutine: "runTest"            # runTest のみ（TestScope不要）
  mock_policy: "strict"           # すべてのモックに明示的設定
  flow_verification: "first"      # first() で単一値検証
  suppress: []                    # 通常不要
```

**特徴**:
- 純粋なビジネスロジックのテスト
- `runTest { }` で直接実行
- `coEvery` / `coVerify` でRepository呼び出しを検証
- `Result<T>` の成功/失敗パターン

### Data 層（Repository / ApiService / Mapper）

```yaml
data:
  assertion: "truth"              # Google Truth が主力
  coroutine: "runTest"            # runTest のみ（TestScope不要）
  mock_policy: "relaxed"          # secondary依存は relaxed
  flow_verification: "first"      # first() で単一値検証
  suppress:
    - "NonAsciiCharacters"
    - "TestFunctionName"
```

**特徴**:
- API/DataSource のモック
- MockWebServer を使った統合テスト
- Mapper は純粋関数（runTest不要）
- Entity⇔DomainModel 変換テスト

### UI 層（ViewModel / StateManager / Presenter / Reducer / Handler）

```yaml
ui:
  assertion: "truth"              # Google Truth が主力
  coroutine: "testScope_runTest"  # testScope.runTest + Dispatchers.setMain 手動管理
  mock_policy: "mixed"            # Reducer: relaxed, UseCase: strict
  flow_verification: "manual_collect"  # mutableListOf + launch collect + advanceUntilIdle
  suppress:
    - "NonAsciiCharacters"
    - "TestFunctionName"
```

**特徴**:
- `TestScope` + `StandardTestDispatcher` 必須
- `Dispatchers.setMain` / `resetMain` の手動管理
- State / Event / Action の Flow 検証
- アナリティクスイベント検証

---

## アサーションライブラリ

使用するアサーションライブラリを指定:

```yaml
assertion:
  # primary: junit | truth | both
  primary: "junit"

  # UI層（ViewModel/StateManager）で Truth を使用するか
  use_truth_for_ui: true
```

**JUnit Assert**:
```kotlin
assertTrue(result.isSuccess)
assertEquals(expected, actual)
assertNotNull(value)
```

**Google Truth**:
```kotlin
assertThat(result.isSuccess).isTrue()
assertThat(actual).isEqualTo(expected)
assertThat(value).isNotNull()
```

---

## Coroutine テスト設定

```yaml
coroutine:
  # dispatcher_rule: standard | main_dispatcher_rule
  dispatcher_rule: "standard"

  # Dispatchers.setMain/resetMain を使用するか
  manual_main_dispatcher: true
```

**standard（デフォルト）**:
```kotlin
private val testDispatcher = StandardTestDispatcher()

@Before
fun setUp() {
    Dispatchers.setMain(testDispatcher)
}

@After
fun tearDown() {
    Dispatchers.resetMain()
}
```

**main_dispatcher_rule**:
```kotlin
@get:Rule
val mainDispatcherRule = MainDispatcherRule()
```

### runTest vs testScope.runTest 使い分け

| 層 | パターン | 理由 |
|----|---------|------|
| Domain (UseCase) | `runTest { }` | TestScope不要、単純なsuspend関数呼び出し |
| Data (Repository) | `runTest { }` | TestScope不要、API呼び出しのモック検証 |
| Data (Mapper) | なし | 純粋関数、コルーチン不使用 |
| UI (Reducer) | なし | 純粋関数、コルーチン不使用 |
| UI (StateManager) | `testScope.runTest { }` | TestScope必須、Flow collect + advanceUntilIdle |
| UI (Presenter) | `testScope.runTest { }` | TestScope必須、複数UseCase + アナリティクス |
| UI (ViewModel - MVI) | `testScope.runTest { }` | TestScope必須、StateManager委譲検証 |
| UI (ViewModel - AAC) | `runTest { }` | LiveData/StateFlow直接検証 |

---

## Flow テスト設定

```yaml
flow:
  # verification: first | collect | turbine
  verification: "collect"
```

**first()（Domain/Data層向け）**:
```kotlin
val result = useCase().first()
assertEquals(expected, result)
```

**collect + advanceUntilIdle（UI層向け）**:
```kotlin
val values = mutableListOf<T>()
val job = launch { flow.collect { values.add(it) } }
advanceUntilIdle()
// assertions
job.cancel()
```

**turbine**:
```kotlin
flow.test {
    assertEquals(expected, awaitItem())
    awaitComplete()
}
```

---

## 命名規則

```yaml
naming:
  # language: english | japanese | mixed
  language: "english"

  # backtick: true | false
  use_backtick: true
```

**english（デフォルト）**:
```kotlin
fun `invoke should return success when repository succeeds`()
```

**japanese**:
```kotlin
fun `リポジトリが成功した場合、成功を返すこと`()
```

**mixed**:
```kotlin
fun `invoke should return success - リポジトリ成功時`()
```

---

## Mock 設定

```yaml
mock:
  # library: mockk（現在はMockKのみサポート）
  library: "mockk"

  # relaxed使用ポリシー: strict | relaxed_for_secondary | mixed
  relaxed_policy: "strict"
```

**strict（デフォルト）**: すべてのモックに明示的な設定が必要
**relaxed_for_secondary**: 主要でない依存関係には `relaxed = true` を使用
**mixed**: Reducer/Handler は relaxed、UseCase は strict

### coEvery vs every 使い分け

| 対象 | 使用する関数 | 理由 |
|------|------------|------|
| suspend関数 | `coEvery` / `coVerify` | コルーチン対応 |
| 通常関数 | `every` / `verify` | 非suspend |
| Flow返却関数 | `every` | Flow自体はsuspendでない |
| Unit返却関数 | `relaxUnitFun = true` | 明示的設定不要 |

```kotlin
// suspend関数
coEvery { repository.getData() } returns Result.success(data)

// 通常関数（Flow返却）
every { useCase.observe() } returns flowOf(data)

// アナリティクス（非suspend、Unit返却）
// → MockKAnnotations.init(this, relaxUnitFun = true) で自動
verify { tracker.trackEvent(any(), any()) }
```

---

## @file:Suppress 自動付与ルール

テストファイルの先頭に自動付与する `@file:Suppress`:

```yaml
suppress:
  # 日本語テスト名を使用する場合
  non_ascii: true     # → @file:Suppress("NonAsciiCharacters")
  test_fn_name: true  # → @file:Suppress("TestFunctionName")
```

```kotlin
// 日本語テスト名を使う場合（mixed / japanese）
@file:Suppress("NonAsciiCharacters", "TestFunctionName")
```

---

## Import aliasing ルール

Entity名とDomainModel名が同名の場合に使用:

```yaml
import_alias:
  enabled: true
  pattern: "{TypeName}Entity"  # data層のEntityに"Entity"サフィックスを付与
```

```kotlin
// 同名クラスの衝突を回避
import jp.co.example.data.entity.Article as ArticleEntity
import jp.co.example.domain.model.Article as ArticleModel
```

---

## 追加 import

プロジェクト固有の追加importを指定:

```yaml
additional_imports:
  - "com.example.app.testing.TestUtils"
  - "com.example.app.testing.FakeData"
```

---

## テストケース生成ルール

```yaml
test_cases:
  # 必ず生成するケース
  required:
    - success
    - failure

  # オプションで生成するケース
  optional:
    - empty_result
    - null_handling
    - boundary_values
```

---

## サンプル設定（dmenu-news）

```yaml
project_name: "dmenu-news"
test_package: "jp.co.nttdocomo.dmenunews"
test_directory: "app/src/test/java"

# モジュール別設定
domain:
  assertion: "junit"
  coroutine: "runTest"
  mock_policy: "strict"
  flow_verification: "first"

data:
  assertion: "truth"
  coroutine: "runTest"
  mock_policy: "relaxed"
  flow_verification: "first"

ui:
  assertion: "truth"
  coroutine: "testScope_runTest"
  mock_policy: "mixed"
  flow_verification: "manual_collect"

# 共通設定
naming:
  language: "mixed"
  use_backtick: true

mock:
  library: "mockk"
  relaxed_policy: "mixed"

suppress:
  non_ascii: true
  test_fn_name: true

import_alias:
  enabled: true

test_cases:
  required:
    - success
    - failure
  optional:
    - empty_result
```
