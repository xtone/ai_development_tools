# Repository テストテンプレート

## 基本構造

```kotlin
package {test_package}

import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import java.io.IOException

class {ClassName}Test {

    // === 依存関係（API/DataSource）===
    private lateinit var {apiName}: {ApiType}

    // === テスト対象 ===
    private lateinit var repository: {ClassName}

    @Before
    fun setup() {
        {apiName} = mockk()
        repository = {ClassNameImpl}({apiName})
    }

    // === テストケース ===

    @Test
    fun `{method} should return success when api succeeds`() = runTest {
        // Given
        val apiResponse = {ApiResponse}(...)
        val expected = {DomainModel}(...)
        coEvery { {apiName}.{apiMethod}() } returns apiResponse

        // When
        val result = repository.{method}()

        // Then
        assertTrue(result.isSuccess)
        assertEquals(expected, result.getOrNull())
    }

    @Test
    fun `{method} should return failure when api throws exception`() = runTest {
        // Given
        val exception = IOException("Network error")
        coEvery { {apiName}.{apiMethod}() } throws exception

        // When
        val result = repository.{method}()

        // Then
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is IOException)
    }

    @Test
    fun `{method} should return failure when api returns error response`() = runTest {
        // Given
        coEvery { {apiName}.{apiMethod}() } returns {ErrorResponse}(...)

        // When
        val result = repository.{method}()

        // Then
        assertTrue(result.isFailure)
    }
}
```

---

## API呼び出しパラメータの検証

```kotlin
@Test
fun `{method} should pass correct parameters to api`() = runTest {
    // Given
    val param1 = {value1}
    val param2 = {value2}
    coEvery {
        {apiName}.{apiMethod}(
            param1 = any(),
            param2 = any()
        )
    } returns {ApiResponse}(...)

    // When
    repository.{method}(param1, param2)

    // Then
    coVerify(exactly = 1) {
        {apiName}.{apiMethod}(
            param1 = param1,
            param2 = param2
        )
    }
}
```

---

## キャッシュ付きRepositoryのパターン

```kotlin
class {ClassName}Test {

    private lateinit var api: {ApiType}
    private lateinit var cache: {CacheType}
    private lateinit var repository: {ClassName}

    @Before
    fun setup() {
        api = mockk()
        cache = mockk(relaxed = true)
        repository = {ClassNameImpl}(api, cache)
    }

    @Test
    fun `{method} should return cached data when available`() = runTest {
        // Given
        val cachedData = {CachedData}(...)
        coEvery { cache.get() } returns cachedData

        // When
        val result = repository.{method}()

        // Then
        assertTrue(result.isSuccess)
        assertEquals(cachedData, result.getOrNull())
        coVerify(exactly = 0) { api.{apiMethod}() }
    }

    @Test
    fun `{method} should fetch from api when cache is empty`() = runTest {
        // Given
        coEvery { cache.get() } returns null
        val apiResponse = {ApiResponse}(...)
        coEvery { api.{apiMethod}() } returns apiResponse

        // When
        val result = repository.{method}()

        // Then
        assertTrue(result.isSuccess)
        coVerify(exactly = 1) { api.{apiMethod}() }
        coVerify(exactly = 1) { cache.save(any()) }
    }

    @Test
    fun `{method} should update cache after fetching from api`() = runTest {
        // Given
        coEvery { cache.get() } returns null
        val apiResponse = {ApiResponse}(...)
        val expected = {DomainModel}(...)
        coEvery { api.{apiMethod}() } returns apiResponse

        // When
        repository.{method}()

        // Then
        coVerify { cache.save(expected) }
    }

    @Test
    fun `{method} with forceRefresh should skip cache`() = runTest {
        // Given
        val cachedData = {CachedData}(...)
        coEvery { cache.get() } returns cachedData
        val apiResponse = {ApiResponse}(...)
        coEvery { api.{apiMethod}() } returns apiResponse

        // When
        val result = repository.{method}(forceRefresh = true)

        // Then
        assertTrue(result.isSuccess)
        coVerify(exactly = 1) { api.{apiMethod}() }
    }
}
```

---

## Flow を返すRepositoryのパターン

```kotlin
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf

@Test
fun `observe should emit data from data source`() = runTest {
    // Given
    val data = {Data}(...)
    coEvery { dataSource.observe() } returns flowOf(data)

    // When
    val result = repository.observe().first()

    // Then
    assertEquals(data, result)
}

@Test
fun `observe should transform api model to domain model`() = runTest {
    // Given
    val apiModel = {ApiModel}(...)
    val expectedDomain = {DomainModel}(...)
    coEvery { dataSource.observe() } returns flowOf(apiModel)

    // When
    val result = repository.observe().first()

    // Then
    assertEquals(expectedDomain, result)
}
```

---

## マッピング検証パターン

```kotlin
@Test
fun `{method} should map api response to domain model correctly`() = runTest {
    // Given
    val apiResponse = {ApiResponse}(
        id = "123",
        title = "Test Title",
        createdAt = "2025-01-01T00:00:00Z"
    )
    coEvery { api.{apiMethod}() } returns apiResponse

    // When
    val result = repository.{method}()

    // Then
    assertTrue(result.isSuccess)
    val domainModel = result.getOrNull()!!
    assertEquals("123", domainModel.id)
    assertEquals("Test Title", domainModel.title)
    assertNotNull(domainModel.createdAt)
}
```

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `com.example.app.data.repository` |
| `{ClassName}` | テスト対象クラス名 | `MyListRepositoryImpl` |
| `{ClassNameImpl}` | 実装クラス名 | `MyListRepositoryImpl` |
| `{apiName}` | API変数名 | `myListApi` |
| `{ApiType}` | API型 | `MyListApi` |
| `{apiMethod}` | API メソッド名 | `getFavoriteArticles` |
| `{method}` | Repository メソッド名 | `getFavoriteArticles` |
| `{ApiResponse}` | APIレスポンス型 | `FavoriteArticlesResponse` |
| `{DomainModel}` | ドメインモデル型 | `FavoriteArticle` |
