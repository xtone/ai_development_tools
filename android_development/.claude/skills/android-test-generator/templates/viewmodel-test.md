# ViewModel テストテンプレート

MVI版（薄いラッパー）とAAC版（フル実装）の2パターンに対応。

> **注意**: StateManagerのテストは `statemanager-test.md` を参照してください。

---

## MVI版 ViewModel（薄いラッパーパターン）

MVI版ViewModelはStateManagerへの委譲のみを行う薄いラッパー。
StateManager をモックして委譲の正しさを検証する。

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import com.google.common.truth.Truth.assertThat
import io.mockk.Ordering
import io.mockk.coVerify
import io.mockk.every
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
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
    private lateinit var stateManager: {StateManagerType}

    // === テスト対象 ===
    private lateinit var viewModel: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)

        stateManager = mockk(relaxed = true)

        viewModel = {ClassName}(stateManager)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // === State委譲テスト ===

    @Test
    fun `state - StateManagerのstateが公開されていること`() = testScope.runTest {
        // Given
        val expectedState = {StateType}(isLoading = false, items = emptyList())
        every { stateManager.state } returns MutableStateFlow(expectedState)

        // When
        val result = viewModel.state.value

        // Then
        assertThat(result).isEqualTo(expectedState)
    }

    // === Intent委譲テスト ===

    @Test
    fun `processIntent - StateManagerにIntentが委譲されること`() = testScope.runTest {
        // When
        viewModel.processIntent({IntentType}.Initialize)
        advanceUntilIdle()

        // Then
        coVerify(exactly = 1) { stateManager.processIntent({IntentType}.Initialize) }
    }

    @Test
    fun `processIntent - 複数のIntentが順序通りに委譲されること`() = testScope.runTest {
        // When
        viewModel.processIntent({IntentType}.Initialize)
        viewModel.processIntent({IntentType}.Refresh)
        advanceUntilIdle()

        // Then
        coVerify(ordering = Ordering.ORDERED) {
            stateManager.processIntent({IntentType}.Initialize)
            stateManager.processIntent({IntentType}.Refresh)
        }
    }

    // === Event委譲テスト ===

    @Test
    fun `events - StateManagerのeventsが公開されていること`() = testScope.runTest {
        // Given
        val eventsFlow = MutableSharedFlow<{EventType}>()
        every { stateManager.events } returns eventsFlow

        val collected = mutableListOf<{EventType}>()
        val job = launch { viewModel.events.collect { collected.add(it) } }
        advanceUntilIdle()

        // When
        eventsFlow.emit({EventType}.NavigateToDetail("123"))
        advanceUntilIdle()

        // Then
        assertThat(collected).contains({EventType}.NavigateToDetail("123"))
        job.cancel()
    }
}
```

---

## AAC版 ViewModel（フル実装パターン）

UseCase を直接呼び出す従来のAAC ViewModelパターン。

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import androidx.arch.core.executor.testing.InstantTaskExecutorRule
import com.google.common.truth.Truth.assertThat
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
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

    // === データロードテスト ===

    @Test
    fun `uiState - データロード成功時、Success状態になること`() = runTest {
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

    @Test
    fun `uiState - データロード失敗時、Error状態になること`() = runTest {
        // Given
        coEvery { {useCaseName}() } returns Result.failure(Exception("error"))

        // When
        viewModel = createViewModel()
        advanceUntilIdle()

        // Then
        assertThat(viewModel.uiState.value).isInstanceOf(
            {ClassName}UiState.Error::class.java
        )
    }
}
```

---

## ユーザーアクションの検証（AAC版）

```kotlin
@Test
fun `onRefresh - データを再取得すること`() = runTest {
    // Given
    val initialData = {Data}(id = "1")
    val refreshedData = {Data}(id = "2")
    coEvery { {useCaseName}() } returnsMany listOf(
        Result.success(initialData),
        Result.success(refreshedData)
    )

    viewModel = createViewModel()
    advanceUntilIdle()

    // When
    viewModel.onRefresh()
    advanceUntilIdle()

    // Then
    val state = viewModel.uiState.value as {ClassName}UiState.Success
    assertThat(state.data).isEqualTo(refreshedData)
    coVerify(exactly = 2) { {useCaseName}() }
}

@Test
fun `onRetry - エラー後にデータを再取得すること`() = runTest {
    // Given
    coEvery { {useCaseName}() } returnsMany listOf(
        Result.failure(Exception()),
        Result.success({data})
    )

    viewModel = createViewModel()
    advanceUntilIdle()

    // エラー状態を確認
    assertThat(viewModel.uiState.value).isInstanceOf(
        {ClassName}UiState.Error::class.java
    )

    // When
    viewModel.onRetry()
    advanceUntilIdle()

    // Then
    assertThat(viewModel.uiState.value).isInstanceOf(
        {ClassName}UiState.Success::class.java
    )
}
```

---

## 複数UseCase依存のパターン（AAC版）

```kotlin
class {ClassName}Test {

    private lateinit var getDataUseCase: GetDataUseCase
    private lateinit var saveDataUseCase: SaveDataUseCase
    private lateinit var viewModel: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        getDataUseCase = mockk()
        saveDataUseCase = mockk()
    }

    private fun createViewModel(): {ClassName} {
        return {ClassName}(getDataUseCase, saveDataUseCase)
    }

    @Test
    fun `onSave - saveDataUseCaseを呼び出すこと`() = runTest {
        // Given
        coEvery { getDataUseCase() } returns Result.success({data})
        viewModel = createViewModel()
        advanceUntilIdle()

        val dataToSave = {Data}(...)
        coEvery { saveDataUseCase(dataToSave) } returns Result.success(Unit)

        // When
        viewModel.onSave(dataToSave)
        advanceUntilIdle()

        // Then
        coVerify(exactly = 1) { saveDataUseCase(dataToSave) }
    }
}
```

---

## 設計ポイント

| 項目 | MVI版（薄いラッパー） | AAC版（フル実装） |
|------|---------------------|-------------------|
| runTest | `testScope.runTest` | `runTest` |
| アサーション | Truth | Truth + JUnit Assert |
| Mock | StateManager を `relaxed = true` | UseCase を `mockk()` |
| Dispatcher | `TestScope` + `setMain/resetMain` | `setMain/resetMain` |
| テスト焦点 | 委譲の正しさ | ビジネスロジック・状態遷移 |

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.ui.mylist` |
| `{ClassName}` | ViewModelクラス名 | `MyListViewModel` |
| `{StateManagerType}` | StateManager型 | `MyListStateManager` |
| `{StateType}` | State型 | `MyListState` |
| `{IntentType}` | Intent sealed class | `MyListIntent` |
| `{EventType}` | Event sealed class | `MyListEvent` |
| `{useCaseName}` | UseCase変数名 | `getArticlesUseCase` |
| `{UseCaseType}` | UseCase型 | `GetArticlesUseCase` |
| `{ClassName}UiState` | UI状態クラス | `MyListUiState` |
| `{ExpectedData}` | 期待するデータ | `listOf(Article(...))` |
