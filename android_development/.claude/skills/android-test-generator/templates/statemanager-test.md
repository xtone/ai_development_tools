# StateManager テストテンプレート

StateManagerはIntent→Action変換とEvent発行を担当する。
TestScope + StandardTestDispatcher を使用し、コルーチン制御下でテストする。

---

## 基本構造

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

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
    private lateinit var reducer: {ReducerType}
    private lateinit var {useCaseName}: {UseCaseType}

    // === テスト対象 ===
    private lateinit var stateManager: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)

        reducer = mockk(relaxed = true)
        {useCaseName} = mockk()

        stateManager = {ClassName}(
            reducer = reducer,
            {useCaseName} = {useCaseName},
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

## Intent→Action 変換テスト（processIntent の戻り値検証）

```kotlin
@Test
fun `processIntent - Initialize を受け取った場合、LoadStart アクションを返すこと`() = testScope.runTest {
    // Given
    coEvery { {useCaseName}() } returns Result.success({expectedData})

    // When
    stateManager.processIntent({IntentType}.Initialize)
    advanceUntilIdle()

    // Then
    coVerify { {useCaseName}() }
}

@Test
fun `processIntent - Refresh を受け取った場合、データを再取得すること`() = testScope.runTest {
    // Given
    val expected = {ExpectedData}(...)
    coEvery { {useCaseName}() } returns Result.success(expected)

    // When
    stateManager.processIntent({IntentType}.Refresh)
    advanceUntilIdle()

    // Then
    coVerify(exactly = 1) { {useCaseName}() }
}

@Test
fun `processIntent - UseCase失敗時、エラーアクションを発行すること`() = testScope.runTest {
    // Given
    val exception = Exception("Network error")
    coEvery { {useCaseName}() } returns Result.failure(exception)

    // When
    stateManager.processIntent({IntentType}.Initialize)
    advanceUntilIdle()

    // Then
    // reducer への LoadFailure アクション発行を検証
    coVerify { reducer.reduce(any(), match { it is {ActionType}.LoadFailure }) }
}
```

---

## Event 発行テスト

SharedFlow/Channel 経由のワンショットイベントを検証:

```kotlin
@Test
fun `processIntent - アイテムクリック時、NavigateToDetail イベントを発行すること`() = testScope.runTest {
    // Given
    val events = mutableListOf<{EventType}>()
    val job = launch { stateManager.events.collect { events.add(it) } }
    advanceUntilIdle()

    // When
    stateManager.processIntent({IntentType}.OnItemClick(itemId = "123"))
    advanceUntilIdle()

    // Then
    assertThat(events).contains({EventType}.NavigateToDetail("123"))
    job.cancel()
}

@Test
fun `processIntent - エラー時、ShowError イベントを発行すること`() = testScope.runTest {
    // Given
    val events = mutableListOf<{EventType}>()
    val job = launch { stateManager.events.collect { events.add(it) } }
    advanceUntilIdle()

    coEvery { {useCaseName}() } returns Result.failure(Exception("error"))

    // When
    stateManager.processIntent({IntentType}.Initialize)
    advanceUntilIdle()

    // Then
    assertThat(events.any { it is {EventType}.ShowError }).isTrue()
    job.cancel()
}
```

---

## State 参照テスト

StateManagerがReducer経由で正しくStateを更新することを検証:

```kotlin
@Test
fun `state - 初期状態が正しいこと`() = testScope.runTest {
    assertThat(stateManager.state.value).isEqualTo({StateType}())
}

@Test
fun `state - Initialize後にデータが反映されること`() = testScope.runTest {
    // Given
    val items = listOf({ItemType}(id = "1"))
    coEvery { {useCaseName}() } returns Result.success(items)

    // Reducer の挙動を設定
    coEvery { reducer.reduce(any(), any()) } answers {
        val currentState = firstArg<{StateType}>()
        currentState.copy(items = items, isLoading = false)
    }

    // When
    stateManager.processIntent({IntentType}.Initialize)
    advanceUntilIdle()

    // Then
    assertThat(stateManager.state.value.items).isEqualTo(items)
}
```

---

## 複数UseCase依存パターン

```kotlin
class {ClassName}Test {

    // 複数のUseCase
    private lateinit var getDataUseCase: GetDataUseCase
    private lateinit var bookmarkUseCase: BookmarkUseCase
    private lateinit var stateManager: {ClassName}

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        testScope = TestScope(testDispatcher)

        reducer = mockk(relaxed = true)
        getDataUseCase = mockk()
        bookmarkUseCase = mockk()

        stateManager = {ClassName}(
            reducer = reducer,
            getDataUseCase = getDataUseCase,
            bookmarkUseCase = bookmarkUseCase,
            scope = testScope
        )
    }

    @Test
    fun `processIntent - Bookmark時、bookmarkUseCaseを呼び出すこと`() = testScope.runTest {
        // Given
        coEvery { bookmarkUseCase(any()) } returns Result.success(Unit)

        // When
        stateManager.processIntent({IntentType}.ToggleBookmark(articleId = "123"))
        advanceUntilIdle()

        // Then
        coVerify(exactly = 1) { bookmarkUseCase("123") }
    }
}
```

---

## 設計ポイント

| 項目 | 値 |
|------|-----|
| runTest | `testScope.runTest` |
| アサーション | Truth (`assertThat`) |
| Mock | MockK（reducer は `relaxed = true`） |
| Dispatcher | `StandardTestDispatcher` + `TestScope` |
| Event検証 | `mutableListOf` + `launch { collect }` + `advanceUntilIdle` |
| 注意点 | reducer は relaxed mock にして StateManager のロジックに集中 |

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.ui.mylist` |
| `{ClassName}` | StateManagerクラス名 | `MyListStateManager` |
| `{ReducerType}` | Reducer型 | `MyListReducer` |
| `{useCaseName}` | UseCase変数名 | `getArticlesUseCase` |
| `{UseCaseType}` | UseCase型 | `GetArticlesUseCase` |
| `{IntentType}` | Intent sealed class | `MyListIntent` |
| `{ActionType}` | Action sealed class | `MyListAction` |
| `{EventType}` | Event sealed class | `MyListEvent` |
| `{StateType}` | State data class | `MyListState` |
| `{ItemType}` | リスト項目の型 | `ArticleItem` |
| `{ExpectedData}` | 期待するデータ | `listOf(Article(...))` |
