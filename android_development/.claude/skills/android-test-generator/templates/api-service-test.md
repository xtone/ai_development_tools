# API Service テストテンプレート（MockWebServer）

MockWebServer を使用した API Service のテスト。
JSON fixture ファイルを使ったレスポンス検証パターン。

---

## 基本構造（ApiTestBase 継承パターン）

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import org.junit.After
import org.junit.Before
import org.junit.Test
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.net.HttpURLConnection

class {ClassName}Test {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var apiService: {ClassName}

    @Before
    fun setUp() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val retrofit = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        apiService = retrofit.create({ClassName}::class.java)
    }

    @After
    fun tearDown() {
        mockWebServer.shutdown()
    }
}
```

---

## JSON fixture を使ったレスポンス設定

```kotlin
private fun loadJsonFromResource(fileName: String): String {
    return javaClass.classLoader!!
        .getResourceAsStream("fixtures/$fileName")!!
        .bufferedReader()
        .readText()
}

private fun enqueueResponse(fileName: String, code: Int = HttpURLConnection.HTTP_OK) {
    val json = loadJsonFromResource(fileName)
    mockWebServer.enqueue(
        MockResponse()
            .setResponseCode(code)
            .setBody(json)
            .addHeader("Content-Type", "application/json")
    )
}
```

---

## 正常系テスト

```kotlin
@Test
fun `{method} - 正常レスポンスの場合、正しくパースされること`() = runTest {
    // Given
    enqueueResponse("{fixture_file}.json")

    // When
    val response = apiService.{method}()

    // Then
    assertThat(response.isSuccessful).isTrue()
    val body = response.body()!!
    assertThat(body.{field}).isEqualTo({expectedValue})
    assertThat(body.items).hasSize({expectedSize})
}

@Test
fun `{method} - リクエストパスが正しいこと`() = runTest {
    // Given
    enqueueResponse("{fixture_file}.json")

    // When
    apiService.{method}(param1 = "value1", param2 = "value2")

    // Then
    val request = mockWebServer.takeRequest()
    assertThat(request.path).isEqualTo("/{expected_path}?param1=value1&param2=value2")
    assertThat(request.method).isEqualTo("GET")
}

@Test
fun `{method} - リクエストヘッダーが正しいこと`() = runTest {
    // Given
    enqueueResponse("{fixture_file}.json")

    // When
    apiService.{method}()

    // Then
    val request = mockWebServer.takeRequest()
    assertThat(request.getHeader("Content-Type")).isEqualTo("application/json")
}
```

---

## 異常系テスト

```kotlin
@Test
fun `{method} - 404エラーの場合、レスポンスコードが404であること`() = runTest {
    // Given
    mockWebServer.enqueue(
        MockResponse()
            .setResponseCode(HttpURLConnection.HTTP_NOT_FOUND)
            .setBody("""{"error": "Not Found"}""")
    )

    // When
    val response = apiService.{method}()

    // Then
    assertThat(response.isSuccessful).isFalse()
    assertThat(response.code()).isEqualTo(404)
}

@Test
fun `{method} - 500エラーの場合、レスポンスコードが500であること`() = runTest {
    // Given
    mockWebServer.enqueue(
        MockResponse()
            .setResponseCode(HttpURLConnection.HTTP_INTERNAL_ERROR)
    )

    // When
    val response = apiService.{method}()

    // Then
    assertThat(response.isSuccessful).isFalse()
    assertThat(response.code()).isEqualTo(500)
}

@Test
fun `{method} - 空レスポンスの場合、正しく処理されること`() = runTest {
    // Given
    enqueueResponse("{fixture_file_empty}.json")

    // When
    val response = apiService.{method}()

    // Then
    assertThat(response.isSuccessful).isTrue()
    assertThat(response.body()!!.items).isEmpty()
}
```

---

## Dispatcher を使った複数エンドポイントテスト

```kotlin
@Test
fun `複数APIを連続呼び出しした場合、それぞれ正しいレスポンスを返すこと`() = runTest {
    // Given
    mockWebServer.dispatcher = object : Dispatcher() {
        override fun dispatch(request: RecordedRequest): MockResponse {
            return when (request.path) {
                "/{path1}" -> MockResponse()
                    .setResponseCode(HttpURLConnection.HTTP_OK)
                    .setBody(loadJsonFromResource("{fixture1}.json"))
                "/{path2}" -> MockResponse()
                    .setResponseCode(HttpURLConnection.HTTP_OK)
                    .setBody(loadJsonFromResource("{fixture2}.json"))
                else -> MockResponse().setResponseCode(HttpURLConnection.HTTP_NOT_FOUND)
            }
        }
    }

    // When
    val response1 = apiService.{method1}()
    val response2 = apiService.{method2}()

    // Then
    assertThat(response1.body()!!.{field}).isEqualTo({expected1})
    assertThat(response2.body()!!.{field}).isEqualTo({expected2})
}
```

---

## POST リクエストのボディ検証

```kotlin
@Test
fun `{method} - POSTリクエストのボディが正しいこと`() = runTest {
    // Given
    enqueueResponse("{fixture_file}.json")
    val requestBody = {RequestBody}(
        title = "Test",
        content = "Content"
    )

    // When
    apiService.{method}(requestBody)

    // Then
    val request = mockWebServer.takeRequest()
    assertThat(request.method).isEqualTo("POST")
    val bodyJson = request.body.readUtf8()
    assertThat(bodyJson).contains("\"title\":\"Test\"")
    assertThat(bodyJson).contains("\"content\":\"Content\"")
}
```

---

## JSON fixture ファイル配置

```
src/test/resources/fixtures/
├── {feature}_success.json        # 正常系レスポンス
├── {feature}_empty.json          # 空レスポンス
└── {feature}_error.json          # エラーレスポンス
```

**fixture例** (`articles_success.json`):
```json
{
  "status": "ok",
  "articles": [
    {
      "id": "1",
      "title": "Test Article",
      "publishedAt": "2025-01-01T00:00:00Z"
    }
  ],
  "totalCount": 1
}
```

---

## 設計ポイント

| 項目 | 値 |
|------|-----|
| runTest | `runTest`（MockWebServerはコルーチン不要だが Retrofit suspend関数のため） |
| アサーション | Truth (`assertThat`) |
| Mock | MockWebServer（実際のHTTP通信をシミュレート） |
| fixture | `src/test/resources/fixtures/` に配置 |
| 注意点 | `mockWebServer.shutdown()` を `@After` で必ず呼ぶ |

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.data.api` |
| `{ClassName}` | APIサービスインターフェース名 | `ArticleApiService` |
| `{method}` | APIメソッド名 | `getArticles` |
| `{fixture_file}` | JSONフィクスチャファイル名 | `articles_success` |
| `{expected_path}` | 期待されるリクエストパス | `api/v1/articles` |
| `{RequestBody}` | リクエストボディ型 | `CreateArticleRequest` |
| `{field}` | レスポンスフィールド名 | `totalCount` |
| `{expectedValue}` | 期待される値 | `1` |
| `{expectedSize}` | 期待されるリストサイズ | `3` |
