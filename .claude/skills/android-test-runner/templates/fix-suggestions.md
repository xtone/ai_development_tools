# Test Fix Suggestion Template

テスト失敗時に修正提案を行う際に使用するテンプレートです。

---

## Template

```markdown
## 🔍 Test Failure Analysis

**Failed Test**: `[TestClassName].[testMethodName]()`

**Error Type**: [NullPointerException | MockKException | AssertionError | etc.]

**Root Cause**:
[テスト失敗の原因を1-2文で明確に説明]

---

## 🛠️ Fix

**File**: `[FilePath]:[LineNumber]`

**Current Code**:
```kotlin
[問題のあるコードスニペットを表示]
```

**Fixed Code**:
```kotlin
[修正後のコードを表示]
```

---

## 💡 Explanation

[詳細な説明:
1. 何が問題だったのか
2. なぜそれが失敗を引き起こしたのか
3. 修正がどのように問題を解決するのか
4. 副作用や考慮事項があるか]

---

## ✅ Verification

修正を適用した後、以下を実行してください:
```bash
./gradlew test --tests "*[TestClassName].[testMethodName]"
```
```

---

## Example 1: NullPointerException

```markdown
## 🔍 Test Failure Analysis

**Failed Test**: `UserRepositoryTest.testGetUser()`

**Error Type**: NullPointerException

**Root Cause**:
Mock `userApi.getUser()` が設定されていないため、デフォルトでnullを返し、Repositoryが結果にアクセスしようとした際にNullPointerExceptionが発生しています。

---

## 🛠️ Fix

**File**: `app/src/test/java/com/example/UserRepositoryTest.kt:15`

**Current Code**:
```kotlin
@Before
fun setup() {
    repository = UserRepository(userApi)
}
```

**Fixed Code**:
```kotlin
@Before
fun setup() {
    every { userApi.getUser() } returns Result.success(mockUser)
    repository = UserRepository(userApi)
}
```

---

## 💡 Explanation

MockKのmockはデフォルトでnullを返します。明示的に `every { ... } returns ...` で動作を定義する必要があります。

`repository.getUser()` が内部で `userApi.getUser()` を呼び出すと、nullが返されるため、結果のプロパティにアクセスしようとした際にNullPointerExceptionが発生します。

`every { userApi.getUser() } returns Result.success(mockUser)` を追加することで、MockKにこのメソッドが呼ばれた時に適切なResultオブジェクトを返すよう指示します。

---

## ✅ Verification

修正を適用した後、以下を実行してください:
```bash
./gradlew test --tests "*UserRepositoryTest.testGetUser"
```
```

---

## Example 2: MockK No Answer Found

```markdown
## 🔍 Test Failure Analysis

**Failed Test**: `LoginViewModelTest.testLoginSuccess()`

**Error Type**: MockKException - no answer found

**Root Cause**:
テストが `loginUseCase.execute()` を呼び出していますが、これはsuspend関数です。しかし、`every` の代わりに `coEvery` を使用していないためMockが設定されていません。

---

## 🛠️ Fix

**File**: `app/src/test/java/com/example/LoginViewModelTest.kt:25`

**Current Code**:
```kotlin
@Before
fun setup() {
    every { loginUseCase.execute(any(), any()) } returns Result.success(mockUser)
}
```

**Fixed Code**:
```kotlin
@Before
fun setup() {
    coEvery { loginUseCase.execute(any(), any()) } returns Result.success(mockUser)
}
```

---

## 💡 Explanation

MockKにおけるsuspend関数は `every` ではなく `coEvery` が必要です:
- `every { ... }` - 通常の関数用
- `coEvery { ... }` - suspend関数用

`execute()` メソッドは `suspend fun execute(...)` として定義されているため、`coEvery` を使用する必要があります。

同様に、検証時も:
- `verify { ... }` - 通常の関数用
- `coVerify { ... }` - suspend関数用

---

## ✅ Verification

修正を適用した後、以下を実行してください:
```bash
./gradlew test --tests "*LoginViewModelTest.testLoginSuccess"
```
```

---

## Example 3: Assertion Failure

```markdown
## 🔍 Test Failure Analysis

**Failed Test**: `UserRepositoryTest.testGetUserReturnsCorrectData()`

**Error Type**: AssertionError

**Root Cause**:
テストは `user.name` が "John" であることを期待していますが、mockは "Jane" を返しています。mockデータがテストのアサーションと一致していません。

---

## 🛠️ Fix

**File**: `app/src/test/java/com/example/UserRepositoryTest.kt:12`

**Current Code**:
```kotlin
private val mockUser = User(id = "1", name = "Jane", email = "jane@example.com")

@Test
fun testGetUserReturnsCorrectData() = runTest {
    every { userApi.getUser() } returns Result.success(mockUser)

    val result = repository.getUser()

    assertEquals("John", result.getOrNull()?.name)
}
```

**Fixed Code**:
```kotlin
private val mockUser = User(id = "1", name = "John", email = "john@example.com")

@Test
fun testGetUserReturnsCorrectData() = runTest {
    every { userApi.getUser() } returns Result.success(mockUser)

    val result = repository.getUser()

    assertEquals("John", result.getOrNull()?.name)
}
```

---

## 💡 Explanation

mockデータはテストが期待するものと一致する必要があります:
- Mock userは `name = "Jane"` を持っていた
- テストは `name = "John"` を期待していた

これはよくあるコピー&ペーストのエラーです。テストを書く際は常に以下を確認してください:
1. mockデータがテストのアサーションと一致している
2. テストデータがテストされるシナリオを表している
3. 変数名が実際の値と一致している

代替の修正方法: "Jane" が正しい値の場合は、代わりにアサーションを更新してください:
```kotlin
assertEquals("Jane", result.getOrNull()?.name)
```

---

## ✅ Verification

修正を適用した後、以下を実行してください:
```bash
./gradlew test --tests "*UserRepositoryTest.testGetUserReturnsCorrectData"
```
```

---

## Key Points for Good Fix Suggestions

1. **具体的に** - 正確なファイルパスと行番号を含める
2. **コンテキストを表示** - 現在のコードと修正後のコードの両方を表示
3. **理由を説明** - 単に修正するだけでなく、根本原因を説明する
4. **検証を含める** - 修正が機能することを確認する方法を伝える
5. **コードブロックを使用** - コードを簡単にコピー&ペーストできるようにする
6. **簡潔に** - 説明を明確で要点を押さえたものにする
7. **パターンにリンク** - 関連する場合は `knowledge/test-failure-patterns.md` を参照する

---

**Version**: v1.0
**Last Updated**: 2025-11-20
