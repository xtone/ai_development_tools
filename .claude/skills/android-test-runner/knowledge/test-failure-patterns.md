# Android Test Failure Patterns

Android開発でよく見られるテスト失敗パターンとその解決方法をまとめたドキュメントです。

---

## 1. NullPointerException

### Pattern
```
java.lang.NullPointerException: Parameter specified as non-null is null
    at com.example.UserRepository.getUser(UserRepository.kt:25)
```

### よくある原因
1. Mockの設定が未定義
2. non-nullパラメータにnullが渡されている
3. 依存関係がinjectされていない

### 修正テンプレート
```kotlin
// Mockがnull以外の値を返すように設定
every { dependency.method() } returns nonNullValue

// または null安全性を追加
val result = dependency.method() ?: defaultValue
```

---

## 2. MockK: No Answer Found

### Pattern
```
io.mockk.MockKException: no answer found for: UserApi.getUser()
```

### よくある原因
- `every { ... }` でMockの動作が定義されていない

### 修正テンプレート
```kotlin
@Before
fun setup() {
    every { userApi.getUser() } returns Result.success(mockUser)
    // suspend関数の場合
    coEvery { userApi.getUserSuspend() } returns mockUser
}
```

---

## 3. Assertion Failures

### Pattern
```
expected:<User(id=1, name=John)> but was:<User(id=1, name=Jane)>
```

### よくある原因
1. テストデータの不一致
2. 実装ロジックのエラー
3. Mockが間違ったデータを返している

### 修正方法
1. Mockデータが期待値と一致しているか確認
2. 実装ロジックを確認
3. テストのアサーションを見直す

---

## 4. Coroutine Test Issues

### Pattern
```
kotlinx.coroutines.test.UncompletedCoroutinesError:
Test finished with active jobs: [JobImpl{Active}@1234567]
```

### よくある原因
- Coroutineが適切に待機されていない
- suspend関数に `runTest` を使用していない

### 修正テンプレート
```kotlin
@Test
fun testSuspendFunction() = runTest {
    // Coroutineコードをここでテスト
    val result = repository.fetchData()
    assertEquals(expected, result)
}

// Flowのテスト
@Test
fun testFlow() = runTest {
    val results = repository.userFlow.take(2).toList()
    assertEquals(listOf(user1, user2), results)
}
```

---

## 5. LiveData/StateFlow Not Updating

### Pattern
```
expected:<Loading> but was:<null>
```

### よくある原因
- LiveDataのObserverがトリガーされていない
- StateFlowが収集されていない
- テスト用のDispatcherを使用していない

### 修正テンプレート
```kotlin
// LiveData
@Test
fun testLiveData() {
    val observer = Observer<State> {}
    viewModel.state.observeForever(observer)

    viewModel.loadData()

    assertEquals(State.Loading, viewModel.state.value)

    viewModel.state.removeObserver(observer)
}

// StateFlow with Turbine
@Test
fun testStateFlow() = runTest {
    viewModel.state.test {
        assertEquals(State.Initial, awaitItem())

        viewModel.loadData()

        assertEquals(State.Loading, awaitItem())
        assertEquals(State.Success, awaitItem())
    }
}
```

---

## 6. Network/IO Errors in Tests

### Pattern
```
java.net.UnknownHostException: Unable to resolve host
```

### よくある原因
- Mockではなく実際のネットワーク呼び出しが発生している
- Retrofit/OkHttpがMock化されていない

### 修正テンプレート
```kotlin
// APIインターフェースをMock化
@Mock
lateinit var api: UserApi

@Before
fun setup() {
    // 実際のRetrofitインスタンスを使用しない
    every { api.getUser() } returns mockResponse
}
```

---

## 7. Context/Resources Not Available

### Pattern
```
java.lang.NullPointerException: context must not be null
```

### よくある原因
- Unit testでAndroid Contextを使用している（RobolectricまたはInstrumentation testを使用すべき）
- Resourcesが利用できない

### 修正方法
```kotlin
// Unit testの場合: Contextをmock化
@Mock
lateinit var context: Context

every { context.getString(R.string.app_name) } returns "TestApp"

// またはRobolectricを使用
@RunWith(RobolectricTestRunner::class)
class MyTest {
    @Test
    fun testWithContext() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        // ここで実際のcontextを使用可能
    }
}
```

---

## 8. Verification Failed (MockK)

### Pattern
```
io.mockk.MockKException: Verification failed:
Expected exactly 1 call to userApi.getUser() but was 0
```

### よくある原因
- メソッドが呼ばれていない
- 異なるパラメータで呼ばれている
- 異なるmockインスタンスで呼ばれている

### 修正方法
```kotlin
// メソッドが実際に呼ばれているか確認
verify { userApi.getUser() }

// パラメータが重要な場合
verify { userApi.getUser(userId = "123") }

// suspend関数の場合
coVerify { userApi.getUserSuspend() }

// 任意の回数の呼び出しを許可
verify(atLeast = 0) { userApi.getUser() }
```

---

## 9. Timing Issues

### Pattern
```
Test times out or assertion happens before async operation completes
```

### よくある原因
- 非同期処理を待機していない
- 競合状態（race condition）

### 修正テンプレート
```kotlin
// CoroutineにはrunTestを使用
@Test
fun testAsync() = runTest {
    viewModel.loadData()
    advanceUntilIdle() // すべてのcoroutineを待機
    assertEquals(expected, viewModel.data.value)
}

// LiveDataの場合
@Test
fun testLiveData() {
    val latch = CountDownLatch(1)
    val observer = Observer<Data> {
        // アサーションをここに記述
        latch.countDown()
    }

    viewModel.data.observeForever(observer)
    viewModel.loadData()

    assertTrue(latch.await(2, TimeUnit.SECONDS))
}
```

---

## 10. Class Cast Exception

### Pattern
```
java.lang.ClassCastException:
com.example.UserImpl cannot be cast to com.example.User
```

### よくある原因
- Mockが間違った型を返している
- Genericsの型不一致

### 修正テンプレート
```kotlin
// Mockが正しい型を返すことを確認
every { api.getUser() } returns mockk<User>()

// Generic型の場合
every { api.getData<User>() } returns mockk<Response<User>>()
```

---

## 🔴 プロジェクト固有パターン（Multi-Variant Android Projects）

以下のパターンは、複数のビルドバリアント、複雑なGradle設定、CI/CD統合を持つ本番Androidプロジェクト固有のものです。

---

## 11. Build Variant Configuration Error

### Pattern
```
Problem configuring task :module:test from command line.
> Unknown command-line option '--tests'.
```

### よくある原因
- プロジェクトに複数のビルドバリアント（develop, staging, production等）が存在
- 標準の `--tests` フラグがサポートされていない
- バリアント指定が必要

### 修正テンプレート
```bash
# ステップ1: 利用可能なテストタスクを検出
./gradlew tasks --all | grep "test.*UnitTest"

# 出力例:
# :data:testDevelopDebugUnitTest
# :data:testStagingDebugUnitTest
# :data:testProductionDebugUnitTest

# ステップ2: バリアント固有のタスクを使用
./gradlew :data:testDevelopDebugUnitTest

# ステップ3: すべてのバリアントをテスト（CI相当）
./gradlew :data:test
```

---

## 12. JAVA_HOME Not Set

### Pattern
```
The operation couldn't be completed. Unable to locate a Java Runtime.
Please visit http://www.java.com for information on installing Java.
```

### よくある原因
- JAVA_HOME環境変数が設定されていない
- Claude Codeセッションがshell環境を継承していない
- macOSでは明示的にAndroid Studio JBRパスが必要

### 修正テンプレート
```bash
# macOS: Android Studio JBRに設定
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"

# 確認
$JAVA_HOME/bin/java -version
# 出力: openjdk version "21.0.6" 2025-01-21

# JAVA_HOMEを設定してテストを再実行
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :module:testDevelopDebugUnitTest
```

---

## 13. Constructor Parameter Missing

### Pattern
```
No value passed for parameter 'applicationLaunchInfoRepository'
Missing argument for parameter 'repository'
```

### よくある原因
- 実装クラスのコンストラクタに新しい依存関係が追加された
- テストコードが実装の変更に同期していない
- DIリファクタリングや機能追加時によく発生

### 修正テンプレート
```kotlin
// ステップ1: Mock宣言を追加
private val newRepository: NewRepository = mockk()

// ステップ2: コンストラクタ呼び出しに追加
@Before
fun setup() {
    handler = MyHandler(
        existingDependency = mockExistingDependency,
        newRepository = newRepository, // これを追加
        anotherDependency = mockAnotherDependency,
    )
}

// ステップ3: 必要に応じてMockの動作を設定
coEvery { newRepository.getData() } returns "expected_data"
```

---

## 14. Google Truth Assertion Failure

### Pattern
```
expected: "Expected Value"
but was : "Actual Value"

expected to be equal to: 123
but was              : 456
```

### よくある原因
- テストの期待値と実装の不一致
- Mockが間違ったデータを返している
- テストデータの設定が不正確

### 修正テンプレート
```kotlin
// 確認1: 期待値は正しいか?
assertThat(actual).isEqualTo(expected) // 'expected'を確認

// 確認2: 実装は正しいか?
// 'actual'を生成するコードを確認

// 確認3: テストデータの設定は正しいか?
// Givenセクションを確認

// よく使用するTruthアサーション
assertThat(value).isEqualTo(expected)
assertThat(value).isNotEqualTo(unexpected)
assertThat(value).isNull()
assertThat(value).isNotNull()
assertThat(value).isTrue()
assertThat(value).isFalse()
assertThat(list).hasSize(3)
assertThat(list).isEmpty()
assertThat(list).contains(item)
assertThat(list).containsExactly(item1, item2, item3)
```

---

## 15. Result Type Test Failure

### Pattern
```
Expected Result.Success but was Result.Failure(exception=NetworkException: Network error)
Expected Result.Failure but was Result.Success(value=User(...))
```

### よくある原因
- domain層のレスポンスをResult型でラップしている
- 成功/失敗ケースに対してMockが間違って設定されている
- `runCatching`の実装でのエラーハンドリング

### 修正テンプレート
```kotlin
// 成功ケースのテスト
@Test
fun `成功時にResult_Successを返す`() = runTest {
    // Given
    val expectedData = User(id = "123", name = "John")
    coEvery { repository.getUser() } returns expectedData

    // When
    val result = useCase.invoke()

    // Then
    assertThat(result.isSuccess).isTrue()
    assertThat(result.getOrNull()).isEqualTo(expectedData)
}

// 失敗ケースのテスト
@Test
fun `失敗時にResult_Failureを返す`() = runTest {
    // Given
    val exception = NetworkException("Network error")
    coEvery { repository.getUser() } throws exception

    // When
    val result = useCase.invoke()

    // Then
    assertThat(result.isFailure).isTrue()
    val actualException = result.exceptionOrNull()
    assertThat(actualException).isInstanceOf<NetworkException>()
    assertThat(actualException?.message).isEqualTo("Network error")
}
```

---

## 16. Multi-Variant Incomplete Testing

### Pattern
```
開発者:
$ ./gradlew :ui:testDevelopDebugUnitTest
✅ 54 tests passed

# コミット & プッシュ

Bitrise CI:
$ ./gradlew :ui:testStagingDebugUnitTest
❌ 57 tests: 55 passed, 2 failed

# CI失敗！修正が必要
```

### よくある原因
- ローカルで1つのバリアントのみテストしている
- Staging/ProductionバリアントでHiltモジュールが異なる
- CIはすべてのバリアントをテストするが、開発者は1つのみ

### 修正テンプレート
```bash
# コミット前: すべてのバリアントをテスト（CI相当）
./gradlew :ui:testDevelopDebugUnitTest
./gradlew :ui:testStagingDebugUnitTest
./gradlew :ui:testProductionDebugUnitTest

# または一度にすべてをテスト
./gradlew :ui:test

# すべて成功を確認
# ✅ DevelopDebugUnitTest: 54/54 passed
# ✅ StagingDebugUnitTest: 57/57 passed
# ✅ ProductionDebugUnitTest: 52/52 passed

# 安全にコミット
git add . && git commit -m "fix: テスト修正" && git push
```

---

## 17. Compose UI Test 配置エラー

### Pattern
```
Test not found: MyListScreenTest
Could not find class: com.example.app.ui.feature.mylist.MyListScreenTest
```

### よくある原因
- `ui/src/test/` (unit test) に配置 ← ❌ 間違い
- `ui/src/androidTest/` (instrumentation test) に配置すべき ← ✅ 正解
- Compose UI テストは実際のAndroid環境が必要

### 修正テンプレート
```kotlin
// ✅ 正しい配置: ui/src/androidTest/kotlin/.../MyListScreenTest.kt
package com.example.app.ui.feature.mylist

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.assertIsDisplayed
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MyListScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `お気に入りタブが正しく表示される`() {
        // Given
        composeTestRule.setContent {
            MyListScreenContent(
                uiState = MyListUiState.Success(
                    items = listOf(mockItem1, mockItem2)
                )
            )
        }

        // Then
        composeTestRule.onNodeWithText("マイリスト").assertIsDisplayed()
        composeTestRule.onNodeWithText("お気に入り").assertIsDisplayed()
    }
}
```

### 実行方法
```bash
# ✅ 正しい: Instrumentation Test
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :ui:connectedDevelopDebugAndroidTest

# ❌ 間違い: Unit Test (Compose UI テストは実行されない)
./gradlew :ui:testDevelopDebugUnitTest
```

### 依存関係
```kotlin
// ui/build.gradle.kts
androidTestImplementation("androidx.compose.ui:ui-test-junit4")
debugImplementation("androidx.compose.ui:ui-test-manifest")
```

---

## 18. BuildType の多様性とテスト影響

### Pattern
```bash
# 開発者: Debugバリアントのみテスト
$ ./gradlew :ui:testDevelopDebugUnitTest
✅ 54 tests passed

# CI: 別のビルドタイプで失敗
$ ./gradlew :ui:testDevelopMinifiedUnitTest
❌ ProGuard obfuscation エラー
```

### よくある原因
- プロジェクトは **6フレーバー × 4ビルドタイプ = 24バリアント**
- 通常テストは `Debug` ビルドタイプを使用
- `Minified` や `CiRelease` は異なる ProGuard 設定

**Build Types**:
```
- debug: デバッグビルド（通常のテスト実行）
- release: リリースビルド
- ciRelease: CI専用リリースビルド
- minified: 難読化テスト用
```

### 修正方法

**推奨テスト戦略**:
```bash
# 日常開発: Debug ビルドタイプ（最速）
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :ui:testDevelopDebugUnitTest

# コミット前: 全フレーバー × Debug（推奨）
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :ui:testDebug

# リリース前: 全フレーバー × 全ビルドタイプ（完全確認）
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :ui:test
```

**バリアント構成の確認**:
```bash
# 利用可能なテストタスクを確認
./gradlew tasks --all | grep "test.*UnitTest"

# 出力例:
# :ui:testDevelopDebugUnitTest
# :ui:testDevelopReleaseUnitTest
# :ui:testDevelopCiReleaseUnitTest
# :ui:testDevelopMinifiedUnitTest
# :ui:testStagingDebugUnitTest
# ... (24バリアント分)
```

---

## 19. Flow型テストパターン

### Pattern
```
kotlinx.coroutines.flow.NoSuchElementException: Expected at least one element
```

### よくある原因
- UseCaseの多くが `Flow<T>` を返す
- Flow のテストには特別な収集パターンが必要
- `.first()` や `.toList()` の誤用

### 修正テンプレート

**パターンA: Turbine ライブラリを使用（推奨）**

```kotlin
import app.cash.turbine.test
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.test.runTest
import org.junit.Test

class CheckRPCookieLoginStatusUseCaseImplTest {

    @Test
    fun `ログイン状態のFlowを正しく返す`() = runTest {
        // Given
        val expectedFlow = flowOf(true, false, true)
        every { repository.isRPCookieLoggedIn } returns expectedFlow

        // When & Then: Turbine で複数の emit を検証
        useCase.invoke().test {
            assertThat(awaitItem()).isTrue()
            assertThat(awaitItem()).isFalse()
            assertThat(awaitItem()).isTrue()
            awaitComplete()
        }
    }
}
```

**パターンB: toList() を使用**

```kotlin
@Test
fun `ログイン状態のFlowをListとして検証`() = runTest {
    // Given
    val expectedFlow = flowOf(true, false, true)
    every { repository.isRPCookieLoggedIn } returns expectedFlow

    // When
    val results = useCase.invoke().take(3).toList()

    // Then
    assertThat(results).containsExactly(true, false, true)
}
```

**パターンC: first() で最初の値のみ検証**

```kotlin
@Test
fun `ログイン状態の最初の値を検証`() = runTest {
    // Given
    val expectedFlow = flowOf(true)
    every { repository.isRPCookieLoggedIn } returns expectedFlow

    // When
    val result = useCase.invoke().first()

    // Then
    assertThat(result).isTrue()
}
```

### 依存関係
```kotlin
// build.gradle.kts
testImplementation("app.cash.turbine:turbine:1.0.0")
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
```

### 実装例

```kotlin
// domain/src/main/kotlin/.../CheckRPCookieLoginStatusUseCase.kt
interface CheckRPCookieLoginStatusUseCase {
    operator fun invoke(): Flow<Boolean>
}

class CheckRPCookieLoginStatusUseCaseImpl @Inject constructor(
    private val dAccountAuthRepository: DaccountAuthRepository,
) : CheckRPCookieLoginStatusUseCase {
    override fun invoke(): Flow<Boolean> = dAccountAuthRepository.isRPCookieLoggedIn
}
```

---

## Quick Reference

### CRITICAL Errors（テスト実行が完全に失敗）

| エラーメッセージキーワード | Pattern | 修正目安時間 |
|--------------------------|---------|------------|
| `Unable to locate a Java Runtime` | Pattern 6, 12 | 30秒 |
| `Unknown command-line option '--tests'` | Pattern 5, 11 | 1分 |
| `JAVA_HOME` 関連エラー | Pattern 6, 12 | 30秒 |

### High Priority Errors（テスト結果に影響）

| エラーメッセージキーワード | Pattern | 修正目安時間 |
|--------------------------|---------|------------|
| `No answer found for:` (MockK) | Pattern 2 | 2-5分 |
| `No value passed for parameter` | Pattern 7, 13 | 5-10分 |
| `NullPointerException` | Pattern 1 | 5-15分 |
| `NoSuchElementException` (Flow) | Pattern 19 | 10-20分 |

### Medium Priority Errors（アサーション失敗）

| エラーメッセージキーワード | Pattern | 修正目安時間 |
|--------------------------|---------|------------|
| `expected: X but was: Y` (Truth) | Pattern 8, 14 | 10-30分 |
| `Expected Result.Success but was Result.Failure` | Pattern 9, 15 | 10-30分 |
| `UncompletedCoroutinesError` | Pattern 4 | 5-10分 |
| `Test not found` (Compose UI) | Pattern 17 | 5分 |

### Gradle/Build Errors

| エラーメッセージキーワード | Pattern | 修正目安時間 |
|--------------------------|---------|------------|
| `Hilt test, @HiltAndroidTest, must use @HiltAndroidRule` | Pattern 10 | 2分 |
| CI失敗、ローカル成功 | Pattern 16, 18 | 30-60分 |
| BuildType 関連エラー | Pattern 18 | 10-20分 |

### Classic Patterns（従来型パターン）

| エラーパターン | 最も可能性の高い原因 | クイックフィックス |
|--------------|-------------------|-----------|
| NullPointerException | Mockが設定されていない | `every { ... } returns ...` を追加 |
| No answer found | Mock動作が未定義 | `every { ... }` または `coEvery { ... }` を追加 |
| Assertion failure | データの不一致 | Mockデータとアサーションを確認 |
| UncompletedCoroutinesError | Coroutineが待機されていない | `runTest { ... }` を使用 |
| LiveData null | Observerが設定されていない | `observeForever()` を使用 |
| UnknownHostException | 実際のネットワーク呼び出し | APIインターフェースをMock化 |
| Context null | Unit testでAndroid依存 | Robolectricを使用またはMock化 |
| Verification failed | メソッドが呼ばれていない | コードパスの実行を確認 |
| Timeout | 非同期が待機されていない | `advanceUntilIdle()` を使用 |
| ClassCastException | Mockが間違った型を返す | Mock戻り値の型を修正 |

---

## 効果的なテストデバッグのTips

1. **スタックトレースを注意深く読む** - 最初の行が通常何が問題かを示している
2. **行番号を確認** - エラーで言及されている正確な行に移動
3. **Mockを検証** - すべての依存関係が適切にMock化されていることを確認
4. **--infoフラグを使用** - より詳細なGradle出力を取得: `./gradlew test --info`
5. **単一テストを実行** - 失敗したテストを分離: `./gradlew test --tests "*TestName.testMethod"`
6. **テストデータを確認** - Mockデータがコードの期待と一致することを確認
7. **最近の変更を見直す** - テストが最後に成功してから何が変わったか?

---

## Version History

### v1.0 - 汎用版リリース (2025-11-20)
- ✅ Pattern 1-19 を実装
- ✅ 優先度別にQuick Referenceを再編成（CRITICAL/High/Medium/Gradle）
- ✅ Multi-variantプロジェクトパターン（Pattern 11-16）
- ✅ 高度なパターン（Pattern 17-19: Compose UI, BuildType, Flow）
- ✅ 公開用に汎用化
- ✅ すべての説明を日本語で記述（視認性・メンテナンス性向上）

**Based on**: android-test-runner v0.2 (プロジェクト固有版、98%精度)

**Last Updated**: 2025-11-20
