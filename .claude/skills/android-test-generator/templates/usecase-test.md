# UseCase テストテンプレート

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

class {ClassName}Test {

    // === 依存関係 ===
    private lateinit var {repositoryName}: {RepositoryType}

    // === テスト対象 ===
    private lateinit var useCase: {ClassName}

    @Before
    fun setup() {
        {repositoryName} = mockk()
        useCase = {ClassNameImpl}({repositoryName})
    }

    // === テストケース ===

    @Test
    fun `invoke should return success when repository succeeds`() = runTest {
        // Given
        val expected = {expectedData}
        coEvery { {repositoryName}.{method}() } returns Result.success(expected)

        // When
        val result = useCase()

        // Then
        assertTrue(result.isSuccess)
        assertEquals(expected, result.getOrNull())
        coVerify(exactly = 1) { {repositoryName}.{method}() }
    }

    @Test
    fun `invoke should return failure when repository fails`() = runTest {
        // Given
        val exception = {ExceptionType}("{error message}")
        coEvery { {repositoryName}.{method}() } returns Result.failure(exception)

        // When
        val result = useCase()

        // Then
        assertTrue(result.isFailure)
        assertEquals(exception, result.exceptionOrNull())
    }

    @Test
    fun `invoke should return empty list when no data exists`() = runTest {
        // Given
        coEvery { {repositoryName}.{method}() } returns Result.success(emptyList())

        // When
        val result = useCase()

        // Then
        assertTrue(result.isSuccess)
        assertTrue(result.getOrNull()!!.isEmpty())
    }
}
```

---

## 引数ありUseCaseのパターン

```kotlin
@Test
fun `invoke should pass parameters to repository`() = runTest {
    // Given
    val param = {paramValue}
    val expected = {expectedData}
    coEvery { {repositoryName}.{method}(param) } returns Result.success(expected)

    // When
    val result = useCase(param)

    // Then
    assertTrue(result.isSuccess)
    coVerify(exactly = 1) { {repositoryName}.{method}(param) }
}

@Test
fun `invoke should handle any parameter with any()`() = runTest {
    // Given
    coEvery {
        {repositoryName}.{method}(
            param1 = any(),
            param2 = any()
        )
    } returns Result.success({expectedData})

    // When
    val result = useCase({param1}, {param2})

    // Then
    assertTrue(result.isSuccess)
}
```

---

## Flow を返すUseCaseのパターン

```kotlin
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf

class {ClassName}Test {

    @Test
    fun `invoke should emit value from repository`() = runTest {
        // Given
        val expected = {expectedData}
        coEvery { {repositoryName}.{method}() } returns flowOf(expected)

        // When
        val result = useCase().first()

        // Then
        assertEquals(expected, result)
    }

    @Test
    fun `invoke should emit multiple values`() = runTest {
        // Given
        val values = listOf({value1}, {value2}, {value3})
        coEvery { {repositoryName}.{method}() } returns flowOf(*values.toTypedArray())

        // When
        val results = mutableListOf<{Type}>()
        val job = launch { useCase().collect { results.add(it) } }
        advanceUntilIdle()

        // Then
        assertEquals(values.size, results.size)
        job.cancel()
    }
}
```

---

## 複数依存関係のパターン

```kotlin
class {ClassName}Test {

    private lateinit var repository1: {Repository1Type}
    private lateinit var repository2: {Repository2Type}
    private lateinit var useCase: {ClassName}

    @Before
    fun setup() {
        repository1 = mockk()
        repository2 = mockk()
        useCase = {ClassNameImpl}(repository1, repository2)
    }

    @Test
    fun `invoke should coordinate multiple repositories`() = runTest {
        // Given
        coEvery { repository1.{method1}() } returns Result.success({data1})
        coEvery { repository2.{method2}(any()) } returns Result.success({data2})

        // When
        val result = useCase()

        // Then
        assertTrue(result.isSuccess)
        coVerify(ordering = Ordering.ORDERED) {
            repository1.{method1}()
            repository2.{method2}(any())
        }
    }
}
```

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `com.example.app.domain.usecase` |
| `{ClassName}` | テスト対象クラス名 | `GetFavoriteArticlesUseCase` |
| `{ClassNameImpl}` | 実装クラス名 | `GetFavoriteArticlesUseCaseImpl` |
| `{repositoryName}` | 依存リポジトリ変数名 | `myListRepository` |
| `{RepositoryType}` | リポジトリ型 | `MyListRepository` |
| `{method}` | 呼び出すメソッド名 | `getFavoriteArticles` |
| `{expectedData}` | 期待するデータ | `listOf(FavoriteArticle(...))` |
| `{ExceptionType}` | 例外の型 | `IOException` |
