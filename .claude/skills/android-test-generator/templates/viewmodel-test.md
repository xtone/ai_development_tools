# ViewModel / StateManager テストテンプレート

## 基本構造（StateManager）

```kotlin
package {test_package}

import com.google.common.truth.Truth.assertThat
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
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
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class {ClassName}Test {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var testScope: TestScope

    // === 依存関係 ===
    private lateinit var {useCaseName}: {UseCaseType}

    // === テスト対象 ===
    private lateinit var stateManager: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)

        {useCaseName} = mockk()
        stateManager = {ClassName}(
            {useCaseName},
            testScope
        )
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // === テストケース ===

    @Test
    fun `initial state should be Loading`() = testScope.runTest {
        assertThat(stateManager.state.value).isEqualTo({ClassName}UiState.Loading)
    }

    @Test
    fun `Initialize intent should trigger data loading`() = testScope.runTest {
        // Given
        val expected = {ExpectedData}(...)
        coEvery { {useCaseName}() } returns Result.success(expected)

        // When
        stateManager.processIntent({ClassName}Intent.Initialize)
        advanceUntilIdle()

        // Then
        assertThat(stateManager.state.value).isEqualTo(
            {ClassName}UiState.Success(expected)
        )
    }

    @Test
    fun `should emit Error state when use case fails`() = testScope.runTest {
        // Given
        val exception = Exception("Error message")
        coEvery { {useCaseName}() } returns Result.failure(exception)

        // When
        stateManager.processIntent({ClassName}Intent.Initialize)
        advanceUntilIdle()

        // Then
        assertThat(stateManager.state.value).isInstanceOf(
            {ClassName}UiState.Error::class.java
        )
    }
}
```

---

## Action/Event発行の検証

```kotlin
@Test
fun `processIntent should emit ShowLoading action`() = testScope.runTest {
    // Given
    val actions = mutableListOf<{ClassName}Action>()
    val job = launch { stateManager.actions.collect { actions.add(it) } }
    advanceUntilIdle()

    // When
    stateManager.processIntent({ClassName}Intent.Initialize)
    advanceUntilIdle()

    // Then
    assertThat(actions).contains({ClassName}Action.ShowLoading)
    job.cancel()
}

@Test
fun `should emit NavigateTo action on item click`() = testScope.runTest {
    // Given
    val actions = mutableListOf<{ClassName}Action>()
    val job = launch { stateManager.actions.collect { actions.add(it) } }
    advanceUntilIdle()

    // When
    stateManager.processIntent({ClassName}Intent.OnItemClick(itemId = "123"))
    advanceUntilIdle()

    // Then
    assertThat(actions).contains(
        {ClassName}Action.NavigateTo("detail/123")
    )
    job.cancel()
}
```

---

## State遷移の検証

```kotlin
@Test
fun `state should transition from Loading to Success`() = testScope.runTest {
    // Given
    val states = mutableListOf<{ClassName}UiState>()
    val job = launch { stateManager.state.collect { states.add(it) } }
    advanceUntilIdle()

    coEvery { {useCaseName}() } returns Result.success({data})

    // When
    stateManager.processIntent({ClassName}Intent.Initialize)
    advanceUntilIdle()

    // Then
    assertThat(states).containsAtLeast(
        {ClassName}UiState.Loading,
        {ClassName}UiState.Success({data})
    ).inOrder()
    job.cancel()
}

@Test
fun `state should transition from Loading to Error on failure`() = testScope.runTest {
    // Given
    val states = mutableListOf<{ClassName}UiState>()
    val job = launch { stateManager.state.collect { states.add(it) } }
    advanceUntilIdle()

    coEvery { {useCaseName}() } returns Result.failure(Exception())

    // When
    stateManager.processIntent({ClassName}Intent.Initialize)
    advanceUntilIdle()

    // Then
    assertThat(states[0]).isEqualTo({ClassName}UiState.Loading)
    assertThat(states.last()).isInstanceOf({ClassName}UiState.Error::class.java)
    job.cancel()
}
```

---

## 基本構造（ViewModel - AAC）

```kotlin
package {test_package}

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import io.mockk.coEvery
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class {ClassName}Test {

    @get:Rule
    val instantTaskExecutorRule = InstantTaskExecutorRule()

    private val testDispatcher = StandardTestDispatcher()

    // === 依存関係 ===
    private lateinit var {useCaseName}: {UseCaseType}

    // === テスト対象 ===
    private lateinit var viewModel: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        {useCaseName} = mockk()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun createViewModel(): {ClassName} {
        return {ClassName}({useCaseName})
    }

    @Test
    fun `uiState should be Success when data loads successfully`() = runTest {
        // Given
        val expected = {ExpectedData}(...)
        coEvery { {useCaseName}() } returns Result.success(expected)

        // When
        viewModel = createViewModel()
        advanceUntilIdle()

        // Then
        val state = viewModel.uiState.value
        assertTrue(state is {ClassName}UiState.Success)
        assertEquals(expected, (state as {ClassName}UiState.Success).data)
    }
}
```

---

## ユーザーアクションの検証

```kotlin
@Test
fun `onRefresh should reload data`() = testScope.runTest {
    // Given
    val initialData = {Data}(id = "1")
    val refreshedData = {Data}(id = "2")
    coEvery { {useCaseName}() } returnsMany listOf(
        Result.success(initialData),
        Result.success(refreshedData)
    )

    stateManager.processIntent({ClassName}Intent.Initialize)
    advanceUntilIdle()

    // When
    stateManager.processIntent({ClassName}Intent.Refresh)
    advanceUntilIdle()

    // Then
    val state = stateManager.state.value as {ClassName}UiState.Success
    assertThat(state.data).isEqualTo(refreshedData)
    coVerify(exactly = 2) { {useCaseName}() }
}

@Test
fun `onRetry should reload data after error`() = testScope.runTest {
    // Given
    coEvery { {useCaseName}() } returnsMany listOf(
        Result.failure(Exception()),
        Result.success({data})
    )

    stateManager.processIntent({ClassName}Intent.Initialize)
    advanceUntilIdle()

    // エラー状態を確認
    assertThat(stateManager.state.value).isInstanceOf(
        {ClassName}UiState.Error::class.java
    )

    // When
    stateManager.processIntent({ClassName}Intent.Retry)
    advanceUntilIdle()

    // Then
    assertThat(stateManager.state.value).isInstanceOf(
        {ClassName}UiState.Success::class.java
    )
}
```

---

## 複数UseCase依存のパターン

```kotlin
class {ClassName}Test {

    private lateinit var getDataUseCase: GetDataUseCase
    private lateinit var saveDataUseCase: SaveDataUseCase
    private lateinit var stateManager: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)

        getDataUseCase = mockk()
        saveDataUseCase = mockk()

        stateManager = {ClassName}(
            getDataUseCase,
            saveDataUseCase,
            testScope
        )
    }

    @Test
    fun `Save intent should call saveDataUseCase`() = testScope.runTest {
        // Given
        val dataToSave = {Data}(...)
        coEvery { saveDataUseCase(dataToSave) } returns Result.success(Unit)

        // When
        stateManager.processIntent({ClassName}Intent.Save(dataToSave))
        advanceUntilIdle()

        // Then
        coVerify(exactly = 1) { saveDataUseCase(dataToSave) }
    }
}
```

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `com.example.app.ui.mylist` |
| `{ClassName}` | テスト対象クラス名 | `MyListStateManager` |
| `{useCaseName}` | UseCase変数名 | `getFavoriteArticlesUseCase` |
| `{UseCaseType}` | UseCase型 | `GetFavoriteArticlesUseCase` |
| `{ClassName}UiState` | UI状態クラス | `MyListUiState` |
| `{ClassName}Intent` | Intentクラス | `MyListIntent` |
| `{ClassName}Action` | Actionクラス | `MyListAction` |
| `{ExpectedData}` | 期待するデータ | `listOf(FavoriteArticle(...))` |
