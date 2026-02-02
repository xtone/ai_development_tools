# Android Test Generator スキル v1.0

## Description

Android実装コードから適切なテストケースを自動生成するスキル。MVI 4層（Reducer / StateManager / Presenter / ViewModel）、Domain層（UseCase）、Data層（Repository / ApiService / Mapper）、横断的関心事（Handler）に対応し、プロジェクトのテストパターンに準拠したテストコードを生成する。

---

## Trigger

以下のようなリクエストで起動:
- 「このクラスのテストを作って」
- 「〇〇UseCaseのテストを生成して」
- 「このファイルのテストケースを作成」
- 「テストを自動生成」

---

## System Instructions

### 1. 実装コードの分析とクラス種別自動判定

テスト対象のクラスを読み込み、以下の判定ロジックで種別を特定する:

```
入力ファイル解析 → 以下のパターンで判定（上から順に評価）:

 1. "fun reduce(state:" 検出
    → Reducer テンプレート（templates/reducer-test.md）

 2. "processIntent" + "handleAction" 検出
    → StateManager テンプレート（templates/statemanager-test.md）

 3. "Presenter" in クラス名 + UseCase依存
    → Presenter テンプレート（templates/presenter-test.md）

 4. "ViewModel" in クラス名 + StateManager依存
    → ViewModel(薄いラッパー) テンプレート（templates/viewmodel-test.md MVI版）

 5. "ViewModel" in クラス名 + UseCase依存
    → ViewModel(AAC) テンプレート（templates/viewmodel-test.md AAC版）

 6. "Handler" in クラス名
    → Handler テンプレート（templates/handler-test.md）

 7. "UseCase" in クラス名
    → UseCase テンプレート（templates/usecase-test.md）

 8. "Repository" in クラス名 + ApiService依存
    → Repository テンプレート（templates/repository-test.md）
    ※ MockWebServerパターンが適切な場合は templates/api-service-test.md も参照

 9. "Repository" in クラス名 + Dao依存
    → Repository(MockK) テンプレート（templates/repository-test.md）

10. "Mapper" in クラス名 or "toXxx()" 拡張関数
    → Mapper テンプレート（templates/mapper-test.md）
```

判定後、以下を特定:
- 依存関係（コンストラクタ引数）
- 公開メソッド（テスト対象）
- 戻り値の型（Result<T> / Flow<T> / 単純な値）

### 2. プロジェクト設定の確認

`knowledge/project-config.md` を読み込み、プロジェクト固有の設定を適用:

- **モジュール別設定**: テスト対象の属する層（Domain/Data/UI）に応じた設定
  - アサーションライブラリ（JUnit Assert / Google Truth）
  - コルーチンパターン（runTest / testScope.runTest）
  - Mockポリシー（strict / relaxed / mixed）
  - Flow検証方法（first / manual_collect）
- 命名規則（日本語/英語）
- 追加のimport

設定ファイルがない場合はデフォルト設定を使用。

### 3. テストコード生成ルール

#### @file:Suppress 自動付与

テスト名に日本語を含む場合（naming: japanese or mixed）、ファイル先頭に自動付与:

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")
```

#### Import aliasing（同名クラス問題）

Entity名とDomainModel名が同名の場合、import aliasを自動適用:

```kotlin
import jp.co.example.data.entity.Article as ArticleEntity
import jp.co.example.domain.model.Article as ArticleModel
```

#### 値クラス（`@JvmInline value class`）の扱い

MockKは `@JvmInline value class` をモックできない（`unbox-impl()` エラーになる）。
値クラスのフィールドには実インスタンスを使用すること:

```kotlin
// NG - MockKで値クラスをモックするとunbox-implエラー
every { article.id } returns mockk<ArticleId>()  // ❌ 失敗

// OK - 実インスタンスを使用
every { article.id } returns ArticleId("article-1")  // ✅ 成功
```

プロジェクトで使われる値クラスの例: `ArticleId`, `CategoryId`, `TabId`, `PhotoId` 等

#### Android Framework依存クラスのテスト制約

`Intent`、`Activity`、`Uri` 等のAndroid Frameworkクラスに依存するメソッドは、
純粋JUnitテストでは制約がある:

- **`Uri.parse()`**: `mockkStatic(Uri::class)` でモック可能
- **`Intent` コンストラクタ**: `returnDefaultValues = true` 未設定の場合 "Method not mocked" エラー
- **`Activity.createIntent()`等の静的メソッド**: Activity クラスのロード自体が失敗する

**対処法（優先順）**:
1. Android Framework非依存のロジック（アナリティクス判定、ブラックリスト判定等）に検証を集中
2. `testOptions.unitTests.returnDefaultValues = true` をbuild.gradleに設定
3. Robolectric を導入して統合テストとして実行

#### ネストされた型参照の注意

APIレスポンスモデルで、別クラスのネスト型を参照しているケースがある:

```kotlin
// GetArticleResponse の rows フィールドが GetTimelineResponse.Row を参照
val rows: List<GetTimelineResponse.Row>?  // ← GetArticleResponse.Row ではない
```

テスト生成時は、フィールドの実際の型定義を確認し、正しいimportを使用すること。

#### coEvery vs every の使い分け

| 対象 | Mock関数 | Verify関数 |
|------|---------|-----------|
| suspend関数（Repository.getData()等） | `coEvery` | `coVerify` |
| 通常関数（UseCase.observe()等） | `every` | `verify` |
| Flow返却関数 | `every` | `verify` |
| Unit返却関数（analytics等） | `relaxUnitFun = true` | `verify` |

#### runTest vs testScope.runTest の使い分け

| 層・種別 | パターン | 理由 |
|---------|---------|------|
| UseCase | `= runTest { }` | 単純なsuspend関数 |
| Repository | `= runTest { }` | API呼び出しモック |
| Mapper | なし | 純粋関数 |
| Reducer | なし | 純粋関数 |
| StateManager | `= testScope.runTest { }` | Flow collect + advanceUntilIdle |
| Presenter | `= testScope.runTest { }` | 複数UseCase + analytics |
| ViewModel (MVI) | `= testScope.runTest { }` | StateManager委譲検証 |
| ViewModel (AAC) | `= runTest { }` | LiveData/StateFlow直接検証 |
| Handler (sync) | なし | 非コルーチン |
| Handler (async) | `= runTest { }` | suspend関数呼び出し |

### 4. テストケース生成

判定されたクラス種別に基づき、対応するテンプレートを使用してテストコードを生成。

各テンプレートで定義された置換プレースホルダーを実装コードの情報で置換する。

### 5. テストメソッド命名規則

**英語パターン（デフォルト）**:
```kotlin
@Test
fun `invoke should return success when repository succeeds`()
```

**日本語パターン**:
```kotlin
@Test
fun `リポジトリが成功した場合、成功を返すこと`()
```

**混在パターン**:
```kotlin
@Test
fun `processIntent - Initialize を受け取った場合、データを読み込むこと`()
```

### 6. Given-When-Then 構造

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

### 7. 必須import

生成するテストには適切なimportを含める:

**共通**:
```kotlin
import io.mockk.mockk
import org.junit.Before
import org.junit.Test
```

**Domain層（UseCase）追加**:
```kotlin
import io.mockk.coEvery
import io.mockk.coVerify
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
```

**Data層（Repository）追加**:
```kotlin
import io.mockk.coEvery
import io.mockk.coVerify
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
```

**Data層（Mapper）**:
```kotlin
import org.junit.Assert.*
// Mock/コルーチン import 不要
```

**Data層（ApiService + MockWebServer）**:
```kotlin
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
```

**UI層（StateManager / Presenter / ViewModel MVI版）追加**:
```kotlin
import com.google.common.truth.Truth.assertThat
import io.mockk.coEvery
import io.mockk.coVerify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
```

**UI層（Reducer）**:
```kotlin
import com.google.common.truth.Truth.assertThat
// Mock/コルーチン import 不要
```

**UI層（Handler）**:
```kotlin
import io.mockk.MockKAnnotations
import io.mockk.impl.annotations.RelaxedMockK
import io.mockk.verify
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

**パターン1: first() で検証（Domain/Data層）**
```kotlin
@Test
fun `should emit expected value`() = runTest {
    coEvery { repository.observe() } returns flowOf(expected)

    val result = useCase().first()

    assertEquals(expected, result)
}
```

**パターン2: collect + advanceUntilIdle で検証（UI層）**
```kotlin
@Test
fun `should emit multiple values`() = testScope.runTest {
    val values = mutableListOf<T>()
    val job = launch { flow.collect { values.add(it) } }
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

### 判定理由
{自動判定で使用したパターン}

### 適用設定
- モジュール: {Domain / Data / UI}
- アサーション: {JUnit Assert / Google Truth}
- コルーチン: {runTest / testScope.runTest / なし}

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

### テンプレート

| テンプレート | 対象 | 層 |
|------------|------|-----|
| `templates/reducer-test.md` | Reducer（純粋関数） | UI |
| `templates/statemanager-test.md` | StateManager（Intent→Action） | UI |
| `templates/presenter-test.md` | Presenter（UseCase + analytics） | UI |
| `templates/viewmodel-test.md` | ViewModel（MVI薄いラッパー / AAC） | UI |
| `templates/handler-test.md` | Handler（横断的関心事） | UI |
| `templates/usecase-test.md` | UseCase | Domain |
| `templates/repository-test.md` | Repository（MockK） | Data |
| `templates/api-service-test.md` | ApiService（MockWebServer） | Data |
| `templates/mapper-test.md` | Mapper（純粋関数） | Data |

### ナレッジ

- `knowledge/project-config.md` - プロジェクト固有設定（モジュール別設定含む）

---

## 関連スキル

- `android-test-runner`: 生成したテストの実行・検証に使用

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2025-12-02 | 初版作成（dmenu-news分析結果に基づく） |
| 2026-02-02 | v1.0: MVI 4層テンプレート追加、Data層テンプレート追加、Handler追加、モジュール別設定、クラス種別自動判定、値クラス/Android Framework制約/ネスト型の実践知見追加 |
