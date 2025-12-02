# Android Test Generator スキル

## Description

Android実装コードから適切なテストケースを自動生成するスキル。UseCase / Repository / ViewModel の各層に対応し、プロジェクトのテストパターンに準拠したテストコードを生成する。

---

## Trigger

以下のようなリクエストで起動:
- 「このクラスのテストを作って」
- 「〇〇UseCaseのテストを生成して」
- 「このファイルのテストケースを作成」
- 「テストを自動生成」

---

## System Instructions

### 1. 実装コードの分析

テスト対象のクラスを読み込み、以下を特定:

```
1. クラスの種類（UseCase / Repository / ViewModel / StateManager）
2. 依存関係（コンストラクタ引数）
3. 公開メソッド（テスト対象）
4. 戻り値の型（Result<T> / Flow<T> / 単純な値）
```

### 2. プロジェクト設定の確認

`knowledge/project-config.md` を読み込み、プロジェクト固有の設定を適用:
- アサーションライブラリ
- Flow検証方法
- 命名規則（日本語/英語）
- 追加のimport

設定ファイルがない場合はデフォルト設定を使用。

### 3. テストケース生成

#### UseCase の場合

```kotlin
class {ClassName}Test {
    // 依存関係のモック
    private lateinit var {dependency}: {DependencyType}
    private lateinit var useCase: {ClassName}

    @Before
    fun setup() {
        {dependency} = mockk()
        useCase = {ClassNameImpl}({dependency})
    }

    // 生成するテストケース:
    // 1. 成功ケース
    // 2. 失敗ケース
    // 3. 境界値ケース（空リスト、null等）
}
```

#### Repository の場合

```kotlin
class {ClassName}Test {
    // API/DataSource のモック
    private lateinit var api: {ApiType}
    private lateinit var repository: {ClassName}

    @Before
    fun setup() {
        api = mockk()
        repository = {ClassNameImpl}(api)
    }

    // 生成するテストケース:
    // 1. API成功ケース
    // 2. API失敗ケース（IOException等）
    // 3. キャッシュ動作（該当する場合）
}
```

#### ViewModel / StateManager の場合

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class {ClassName}Test {
    private val testDispatcher = StandardTestDispatcher()
    private lateinit var testScope: TestScope
    // 依存関係のモック
    private lateinit var viewModel: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)
        // モック初期化
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // 生成するテストケース:
    // 1. 初期化時の動作
    // 2. Intent/Action処理
    // 3. State遷移
}
```

### 4. テストメソッド命名規則

**英語パターン（デフォルト）**:
```kotlin
@Test
fun `invoke should return success when repository succeeds`()

@Test
fun `invoke should return failure when repository fails`()
```

**日本語パターン**:
```kotlin
@Test
fun `リポジトリが成功した場合、成功を返すこと`()

@Test
fun `リポジトリが失敗した場合、失敗を返すこと`()
```

### 5. Given-When-Then 構造

すべてのテストメソッドは以下の構造で生成:

```kotlin
@Test
fun `テスト名`() = runTest {
    // Given - 前提条件のセットアップ
    val expected = ...
    coEvery { repository.method() } returns Result.success(expected)

    // When - テスト対象の実行
    val result = useCase()

    // Then - 結果の検証
    assertTrue(result.isSuccess)
    assertEquals(expected, result.getOrNull())
    coVerify(exactly = 1) { repository.method() }
}
```

### 6. 必須import

生成するテストには以下のimportを含める:

```kotlin
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
```

**ViewModel/StateManager追加import**:
```kotlin
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
```

**Google Truth使用時**:
```kotlin
import com.google.common.truth.Truth.assertThat
```

---

## 生成パターン詳細

### Result<T> を返すメソッド

| ケース | Mock設定 | アサーション |
|-------|---------|------------|
| 成功 | `returns Result.success(data)` | `assertTrue(result.isSuccess)` |
| 失敗 | `returns Result.failure(exception)` | `assertTrue(result.isFailure)` |
| 空 | `returns Result.success(emptyList())` | `assertTrue(result.getOrNull()!!.isEmpty())` |

### Flow<T> を返すメソッド

**パターン1: first() で検証**
```kotlin
@Test
fun `should emit expected value`() = runTest {
    coEvery { repository.observe() } returns flowOf(expected)

    val result = useCase().first()

    assertEquals(expected, result)
}
```

**パターン2: collect + advanceUntilIdle で検証**
```kotlin
@Test
fun `should emit multiple values`() = runTest {
    val values = mutableListOf<T>()
    val job = launch { useCase().collect { values.add(it) } }
    advanceUntilIdle()

    assertThat(values).hasSize(expectedSize)
    job.cancel()
}
```

---

## 出力フォーマット

生成完了後、以下の形式で出力:

```markdown
## テスト生成完了

### 対象クラス
{ClassName} ({クラス種別})

### 生成したテストケース
1. {テストメソッド名1}
2. {テストメソッド名2}
3. {テストメソッド名3}

### ファイル出力先
{テストファイルパス}

### 追加が推奨されるテストケース
- {手動で追加すべきケースがあれば}
```

---

## 関連ファイル

- `knowledge/project-config.md` - プロジェクト固有設定
- `knowledge/test-patterns.md` - テストパターン詳細
- `templates/usecase-test.md` - UseCaseテストテンプレート
- `templates/repository-test.md` - Repositoryテストテンプレート
- `templates/viewmodel-test.md` - ViewModelテストテンプレート

---

## 関連スキル

- `android-test-runner`: 生成したテストの実行・検証に使用

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-12-02 | 初版作成（dmenu-news分析結果に基づく） |
