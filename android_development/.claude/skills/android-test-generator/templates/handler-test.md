# Handler テストテンプレート

Handlerはアナリティクス送信・ディープリンク処理・ログ出力など横断的関心事を担当する。
MockKAnnotations.init + @RelaxedMockK アノテーションパターンを使用。

---

## 基本構造

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import io.mockk.MockKAnnotations
import io.mockk.RelaxedMockK
import io.mockk.every
import io.mockk.impl.annotations.RelaxedMockK
import io.mockk.mockk
import io.mockk.verify
import org.junit.Before
import org.junit.Test

class {ClassName}Test {

    // === 依存関係（@RelaxedMockK）===
    @RelaxedMockK
    private lateinit var {dependency1Name}: {Dependency1Type}

    @RelaxedMockK
    private lateinit var {dependency2Name}: {Dependency2Type}

    // === テスト対象 ===
    private lateinit var handler: {ClassName}

    @Before
    fun setUp() {
        MockKAnnotations.init(this, relaxUnitFun = true)

        handler = {ClassName}(
            {dependency1Name} = {dependency1Name},
            {dependency2Name} = {dependency2Name}
        )
    }
}
```

---

## アナリティクスイベント送信テスト

```kotlin
@Test
fun `handle - イベントが正しいパラメータで送信されること`() {
    // Given
    val eventData = {EventData}(
        articleId = "123",
        category = "news",
        action = "click"
    )

    // When
    handler.handle(eventData)

    // Then
    verify(exactly = 1) {
        {dependency1Name}.trackEvent(
            eventName = eq("article_click"),
            params = match {
                it["article_id"] == "123" &&
                it["category"] == "news" &&
                it["action"] == "click"
            }
        )
    }
}

@Test
fun `handle - 画面表示イベントが送信されること`() {
    // When
    handler.onScreenView("{screenName}")

    // Then
    verify(exactly = 1) {
        {dependency1Name}.trackScreenView("{screenName}")
    }
}

@Test
fun `handle - 複数のトラッカーに同時送信されること`() {
    // Given
    val eventData = {EventData}(action = "purchase")

    // When
    handler.handle(eventData)

    // Then
    verify(exactly = 1) { {dependency1Name}.trackEvent(any(), any()) }
    verify(exactly = 1) { {dependency2Name}.logEvent(any()) }
}
```

---

## 引数マッチャーを使った検証

```kotlin
@Test
fun `handle - anyマッチャーで呼び出しを検証`() {
    // When
    handler.handle({EventData}(articleId = "123"))

    // Then
    verify { {dependency1Name}.trackEvent(any(), any()) }
}

@Test
fun `handle - match式で部分一致を検証`() {
    // When
    handler.handle({EventData}(
        articleId = "123",
        category = "news",
        position = 5
    ))

    // Then
    verify {
        {dependency1Name}.trackEvent(
            eventName = any(),
            params = match { params ->
                params.containsKey("article_id") &&
                params["position"] == "5"
            }
        )
    }
}

@Test
fun `handle - captureで引数を取得して検証`() {
    // Given
    val paramsSlot = slot<Map<String, String>>()

    // When
    handler.handle({EventData}(articleId = "123", category = "news"))

    // Then
    verify {
        {dependency1Name}.trackEvent(
            eventName = any(),
            params = capture(paramsSlot)
        )
    }
    val captured = paramsSlot.captured
    assertThat(captured["article_id"]).isEqualTo("123")
    assertThat(captured["category"]).isEqualTo("news")
}
```

---

## 条件分岐テスト

```kotlin
@Test
fun `handle - フラグがONの場合のみイベントを送信すること`() {
    // Given
    every { {dependency2Name}.isEnabled() } returns true

    // When
    handler.handle({EventData}(action = "click"))

    // Then
    verify(exactly = 1) { {dependency1Name}.trackEvent(any(), any()) }
}

@Test
fun `handle - フラグがOFFの場合はイベントを送信しないこと`() {
    // Given
    every { {dependency2Name}.isEnabled() } returns false

    // When
    handler.handle({EventData}(action = "click"))

    // Then
    verify(exactly = 0) { {dependency1Name}.trackEvent(any(), any()) }
}
```

---

## ディープリンクHandler パターン

```kotlin
class {DeepLinkHandlerClass}Test {

    @RelaxedMockK
    private lateinit var router: {RouterType}

    @RelaxedMockK
    private lateinit var analyticsTracker: {AnalyticsType}

    private lateinit var handler: {DeepLinkHandlerClass}

    @Before
    fun setUp() {
        MockKAnnotations.init(this, relaxUnitFun = true)
        handler = {DeepLinkHandlerClass}(router, analyticsTracker)
    }

    @Test
    fun `handle - 記事ディープリンクの場合、記事詳細画面に遷移すること`() {
        // Given
        val deepLink = "app://article/123"

        // When
        handler.handle(deepLink)

        // Then
        verify(exactly = 1) { router.navigateTo("article_detail", match { it["id"] == "123" }) }
    }

    @Test
    fun `handle - 不明なディープリンクの場合、ホーム画面に遷移すること`() {
        // Given
        val deepLink = "app://unknown/path"

        // When
        handler.handle(deepLink)

        // Then
        verify(exactly = 1) { router.navigateTo("home", any()) }
    }
}
```

---

## Coroutine を使う Handler

suspend関数を含むHandlerの場合:

```kotlin
import io.mockk.coEvery
import io.mockk.coVerify
import kotlinx.coroutines.test.runTest

@Test
fun `handle - 非同期イベント送信が成功すること`() = runTest {
    // Given
    coEvery { {dependency1Name}.sendAsync(any()) } returns Result.success(Unit)

    // When
    handler.handleAsync({EventData}(action = "purchase"))

    // Then
    coVerify(exactly = 1) { {dependency1Name}.sendAsync(any()) }
}
```

---

## 設計ポイント

| 項目 | 値 |
|------|-----|
| runTest | 基本不要（suspend関数がある場合のみ `runTest`） |
| アサーション | MockK `verify` が主力、値検証は Truth |
| Mock | `MockKAnnotations.init(this, relaxUnitFun = true)` + `@RelaxedMockK` |
| 検証方法 | `verify` + 引数マッチャー（`eq`, `match`, `any`, `capture`） |
| 注意点 | Unit返却関数は `relaxUnitFun = true` で自動リラックス |

## 実プロジェクトでの注意事項

### Android Framework 依存

Intent/Activity/Context に依存するHandler（画面遷移Handler、ディープリンクHandler等）は
純粋JUnitテストに制約がある:

- `Intent` コンストラクタ、`Activity.createIntent()` 等は Android ランタイムが必要
- `Uri.parse()` は `mockkStatic(Uri::class)` でモック可能
- `Timber.d()` はテスト用 Tree を plant するか `mockkStatic` で対応

**推奨アプローチ**: Android非依存のロジック（アナリティクス送信判定、ブラックリスト判定、
条件分岐ロジック等）に検証を集中し、Intent生成・画面遷移は Robolectric 導入後にテスト。

```kotlin
// Uri.parse モック
mockkStatic(Uri::class)
every { Uri.parse(any()) } returns mockk(relaxed = true)

// Timber モック
Timber.plant(object : Timber.Tree() {
    override fun log(priority: Int, tag: String?, message: String, t: Throwable?) {}
})

// tearDown で必ずクリーンアップ
@After
fun tearDown() {
    Timber.uprootAll()
    unmockkAll()
}
```

### 値クラス（`@JvmInline value class`）

`ArticleId`, `CategoryId` 等の値クラスはMockKでモックできない。実インスタンスを使用:

```kotlin
// NG
every { item.id } returns mockk<ArticleId>()  // unbox-impl エラー

// OK
every { item.id } returns ArticleId("article-1")
```

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.ui.handler` |
| `{ClassName}` | Handlerクラス名 | `ArticleAnalyticsHandler` |
| `{dependency1Name}` | 依存変数名1 | `analyticsTracker` |
| `{Dependency1Type}` | 依存型1 | `AnalyticsTracker` |
| `{dependency2Name}` | 依存変数名2 | `featureFlag` |
| `{Dependency2Type}` | 依存型2 | `FeatureFlag` |
| `{EventData}` | イベントデータ型 | `AnalyticsEvent` |
| `{screenName}` | 画面名 | `article_list` |
| `{DeepLinkHandlerClass}` | ディープリンクHandler | `DeepLinkHandler` |
| `{RouterType}` | ルーター型 | `AppRouter` |
| `{AnalyticsType}` | アナリティクス型 | `AnalyticsTracker` |
