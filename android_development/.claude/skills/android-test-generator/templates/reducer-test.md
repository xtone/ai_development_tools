# Reducer テストテンプレート

Reducerは純粋関数であり、`runTest` やコルーチン設定は不要。
入力（現在のState + Action）に対して期待されるStateを返すことを検証する。

---

## 基本構造

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import com.google.common.truth.Truth.assertThat
import org.junit.Before
import org.junit.Test

class {ClassName}Test {

    // === テスト対象 ===
    private lateinit var reducer: {ClassName}

    @Before
    fun setUp() {
        reducer = {ClassName}()
    }

    // === 状態遷移テスト ===

    @Test
    fun `reduce - {Action} を受け取った場合、{期待される状態} になること`() {
        // Given
        val currentState = {StateType}(
            isLoading = false,
            items = emptyList()
        )
        val action = {ActionType}.{ActionName}

        // When
        val newState = reducer.reduce(currentState, action)

        // Then
        assertThat(newState.isLoading).isTrue()
    }

    @Test
    fun `reduce - LoadSuccess を受け取った場合、データが設定されること`() {
        // Given
        val currentState = {StateType}(isLoading = true)
        val items = listOf({ItemType}(id = "1", title = "Test"))
        val action = {ActionType}.LoadSuccess(items)

        // When
        val newState = reducer.reduce(currentState, action)

        // Then
        assertThat(newState.isLoading).isFalse()
        assertThat(newState.items).isEqualTo(items)
    }

    @Test
    fun `reduce - LoadFailure を受け取った場合、エラー状態になること`() {
        // Given
        val currentState = {StateType}(isLoading = true)
        val error = Exception("Network error")
        val action = {ActionType}.LoadFailure(error)

        // When
        val newState = reducer.reduce(currentState, action)

        // Then
        assertThat(newState.isLoading).isFalse()
        assertThat(newState.error).isEqualTo(error)
    }
}
```

---

## 冪等性テスト

同じActionを2回適用しても結果が変わらないことを検証:

```kotlin
@Test
fun `reduce - 同じActionを2回適用しても結果が変わらないこと`() {
    // Given
    val initialState = {StateType}()
    val action = {ActionType}.{ActionName}

    // When
    val state1 = reducer.reduce(initialState, action)
    val state2 = reducer.reduce(state1, action)

    // Then
    assertThat(state1).isEqualTo(state2)
}
```

---

## 複数Action連続適用テスト

```kotlin
@Test
fun `reduce - Loading → LoadSuccess の連続適用で正しい状態になること`() {
    // Given
    val initialState = {StateType}()
    val items = listOf({ItemType}(id = "1"))

    // When
    val loadingState = reducer.reduce(initialState, {ActionType}.StartLoading)
    val successState = reducer.reduce(loadingState, {ActionType}.LoadSuccess(items))

    // Then
    assertThat(loadingState.isLoading).isTrue()
    assertThat(successState.isLoading).isFalse()
    assertThat(successState.items).hasSize(1)
}
```

---

## 部分更新テスト

既存Stateの他のフィールドが保持されることを検証:

```kotlin
@Test
fun `reduce - LoadSuccess で既存のフィルター設定が保持されること`() {
    // Given
    val currentState = {StateType}(
        isLoading = true,
        filterType = FilterType.FAVORITES,
        selectedTab = 2
    )
    val items = listOf({ItemType}(id = "1"))
    val action = {ActionType}.LoadSuccess(items)

    // When
    val newState = reducer.reduce(currentState, action)

    // Then
    assertThat(newState.items).isEqualTo(items)
    assertThat(newState.filterType).isEqualTo(FilterType.FAVORITES)
    assertThat(newState.selectedTab).isEqualTo(2)
}
```

---

## 設計ポイント

| 項目 | 値 |
|------|-----|
| runTest | **不要**（純粋関数） |
| アサーション | Truth (`assertThat`) |
| Mock | **不要**（依存関係なし） |
| テストパターン | `[前State] + [Action] → [次State]` |
| 注意点 | 副作用がないことを前提とする |

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.ui.mylist` |
| `{ClassName}` | Reducerクラス名 | `MyListReducer` |
| `{StateType}` | State型 | `MyListState` |
| `{ActionType}` | Action sealed class | `MyListAction` |
| `{ActionName}` | 具体的なAction | `StartLoading` |
| `{ItemType}` | リスト項目の型 | `ArticleItem` |
