# Presenter テストテンプレート

PresenterはUseCase呼び出し・データ加工・アナリティクスイベント送信を担当する。
TestScope + Dispatchers.setMain/resetMain の手動管理パターンを使用。

---

## 基本構造

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import com.google.common.truth.Truth.assertThat
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class {ClassName}Test {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var testScope: TestScope

    // === 依存関係 ===
    private lateinit var {useCase1Name}: {UseCase1Type}
    private lateinit var {useCase2Name}: {UseCase2Type}
    private lateinit var analyticsTracker: {AnalyticsTrackerType}

    // === テスト対象 ===
    private lateinit var presenter: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)

        {useCase1Name} = mockk()
        {useCase2Name} = mockk()
        analyticsTracker = mockk(relaxUnitFun = true)

        presenter = {ClassName}(
            {useCase1Name} = {useCase1Name},
            {useCase2Name} = {useCase2Name},
            analyticsTracker = analyticsTracker,
            scope = testScope
        )
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }
}
```

---

## データロードテスト（UseCase呼び出し検証）

```kotlin
@Test
fun `loadData - 成功時、UIにデータが反映されること`() = testScope.runTest {
    // Given
    val articles = listOf({ArticleType}(id = "1", title = "Test Article"))
    coEvery { {useCase1Name}() } returns Result.success(articles)

    // When
    presenter.loadData()
    advanceUntilIdle()

    // Then
    assertThat(presenter.uiState.value.articles).isEqualTo(articles)
    assertThat(presenter.uiState.value.isLoading).isFalse()
}

@Test
fun `loadData - 失敗時、エラー状態になること`() = testScope.runTest {
    // Given
    val exception = Exception("Network error")
    coEvery { {useCase1Name}() } returns Result.failure(exception)

    // When
    presenter.loadData()
    advanceUntilIdle()

    // Then
    assertThat(presenter.uiState.value.error).isNotNull()
    assertThat(presenter.uiState.value.isLoading).isFalse()
}
```

---

## Flow返却UseCaseのテスト

```kotlin
@Test
fun `observe - Flowからデータを受信してUIに反映すること`() = testScope.runTest {
    // Given
    val item1 = {ItemType}(id = "1")
    val item2 = {ItemType}(id = "2")
    every { {useCase2Name}() } returns flowOf(listOf(item1), listOf(item1, item2))

    // When
    presenter.startObserving()
    advanceUntilIdle()

    // Then
    assertThat(presenter.uiState.value.items).hasSize(2)
}

@Test
fun `observe - Flow購読中にエラーが発生した場合、エラーハンドリングすること`() = testScope.runTest {
    // Given
    every { {useCase2Name}() } returns kotlinx.coroutines.flow.flow {
        emit(listOf({ItemType}(id = "1")))
        throw Exception("Stream error")
    }

    // When
    presenter.startObserving()
    advanceUntilIdle()

    // Then
    assertThat(presenter.uiState.value.error).isNotNull()
}
```

---

## アナリティクスイベント検証

```kotlin
@Test
fun `onItemClick - アナリティクスイベントを送信すること`() = testScope.runTest {
    // Given
    val articleId = "123"
    val articleTitle = "Test Article"

    // When
    presenter.onItemClick(articleId, articleTitle)
    advanceUntilIdle()

    // Then
    verify(exactly = 1) {
        analyticsTracker.trackEvent(
            eventName = "article_click",
            params = match {
                it["article_id"] == articleId && it["article_title"] == articleTitle
            }
        )
    }
}

@Test
fun `onScreenView - 画面表示イベントを送信すること`() = testScope.runTest {
    // When
    presenter.onScreenView()
    advanceUntilIdle()

    // Then
    verify(exactly = 1) {
        analyticsTracker.trackScreenView("{ScreenName}")
    }
}

@Test
fun `onBookmark - ブックマークイベントとUseCase呼び出しの両方を実行すること`() = testScope.runTest {
    // Given
    val articleId = "123"
    coEvery { {useCase2Name}(articleId) } returns Result.success(Unit)

    // When
    presenter.onBookmark(articleId)
    advanceUntilIdle()

    // Then
    coVerify(exactly = 1) { {useCase2Name}(articleId) }
    verify(exactly = 1) {
        analyticsTracker.trackEvent(
            eventName = "bookmark_toggle",
            params = match { it["article_id"] == articleId }
        )
    }
}
```

---

## 複数UseCase連携テスト

```kotlin
@Test
fun `loadData - 複数UseCaseを並行呼び出しして結果を統合すること`() = testScope.runTest {
    // Given
    val articles = listOf({ArticleType}(id = "1"))
    val categories = listOf({CategoryType}(id = "cat1"))
    coEvery { {useCase1Name}() } returns Result.success(articles)
    coEvery { {useCase2Name}() } returns Result.success(categories)

    // When
    presenter.loadData()
    advanceUntilIdle()

    // Then
    assertThat(presenter.uiState.value.articles).isEqualTo(articles)
    assertThat(presenter.uiState.value.categories).isEqualTo(categories)
}

@Test
fun `loadData - 一方のUseCaseが失敗しても他方の結果は反映すること`() = testScope.runTest {
    // Given
    val articles = listOf({ArticleType}(id = "1"))
    coEvery { {useCase1Name}() } returns Result.success(articles)
    coEvery { {useCase2Name}() } returns Result.failure(Exception("error"))

    // When
    presenter.loadData()
    advanceUntilIdle()

    // Then
    assertThat(presenter.uiState.value.articles).isEqualTo(articles)
    assertThat(presenter.uiState.value.partialError).isTrue()
}
```

---

## 設計ポイント

| 項目 | 値 |
|------|-----|
| runTest | `testScope.runTest` |
| アサーション | Truth (`assertThat`) |
| Mock | MockK（analyticsTracker は `relaxUnitFun = true`） |
| Dispatcher | `StandardTestDispatcher` + `TestScope` + `Dispatchers.setMain/resetMain` 手動管理 |
| coEvery vs every | suspend関数 → `coEvery`、通常関数（Flow返却等） → `every` |
| 注意点 | アナリティクス検証は `verify`（非suspend）、UseCase呼び出しは `coVerify` |

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.ui.article` |
| `{ClassName}` | Presenterクラス名 | `ArticleDetailPresenter` |
| `{useCase1Name}` | UseCase1変数名 | `getArticleDetailUseCase` |
| `{UseCase1Type}` | UseCase1型 | `GetArticleDetailUseCase` |
| `{useCase2Name}` | UseCase2変数名 | `bookmarkArticleUseCase` |
| `{UseCase2Type}` | UseCase2型 | `BookmarkArticleUseCase` |
| `{AnalyticsTrackerType}` | アナリティクス型 | `AnalyticsTracker` |
| `{ScreenName}` | 画面名 | `article_detail` |
| `{ArticleType}` | 記事モデル型 | `ArticleDetail` |
| `{CategoryType}` | カテゴリ型 | `Category` |
| `{ItemType}` | アイテム型 | `ArticleItem` |
