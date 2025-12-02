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

## アサーションライブラリ

使用するアサーションライブラリを指定:

```yaml
assertion:
  # primary: junit | truth | both
  primary: "junit"

  # UI層（ViewModel/StateManager）で Truth を使用するか
  use_truth_for_ui: true
```

**JUnit Assert（デフォルト）**:
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

---

## Flow テスト設定

```yaml
flow:
  # verification: collect | turbine
  verification: "collect"
```

**collect（デフォルト）**:
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

  # relaxed使用ポリシー: strict | relaxed_for_secondary
  relaxed_policy: "strict"
```

**strict（デフォルト）**: すべてのモックに明示的な設定が必要
**relaxed_for_secondary**: 主要でない依存関係には `relaxed = true` を使用

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

assertion:
  primary: "junit"
  use_truth_for_ui: true

coroutine:
  dispatcher_rule: "standard"
  manual_main_dispatcher: true

flow:
  verification: "collect"

naming:
  language: "mixed"
  use_backtick: true

mock:
  library: "mockk"
  relaxed_policy: "strict"

test_cases:
  required:
    - success
    - failure
  optional:
    - empty_result
```
