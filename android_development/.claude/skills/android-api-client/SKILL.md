---
name: android-api-client
description: |
  Retrofit + OkHttpを使用したAPIクライアント実装のベストプラクティスを提供する。
  「API実装」「APIクライアント」「Retrofit」「OkHttp」「ネットワーク」と言われたら使う。
---

# Android APIクライアント実装ガイドライン

Retrofit + OkHttpを使用したAPIクライアント実装のベストプラクティス。

## クイックリファレンス

### 技術スタック
```kotlin
// Retrofit + OkHttp + Kotlinx Serialization
implementation("com.squareup.retrofit2:retrofit:2.9.0")
implementation("com.squareup.retrofit2:converter-kotlinx-serialization:2.9.0")
implementation("com.squareup.okhttp3:okhttp:4.12.0")
implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")
```

### アーキテクチャ
```
UI Layer (ViewModel)
    ↓
Domain Layer (UseCase / Repository Interface)
    ↓
Data Layer (Repository Implementation → API Service → OkHttpClient)
```

### API Service定義
```kotlin
interface ApiService {
    @GET("users")
    suspend fun getUsers(@Query("page") page: Int): List<UserDto>

    @GET("users/{id}")
    suspend fun getUser(@Path("id") userId: String): UserDto

    @POST("users")
    suspend fun createUser(@Body request: CreateUserRequest): UserDto
}
```

### エラーハンドリング（ApiResult型）
```kotlin
sealed interface ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>
    data class Error(val error: ApiError) : ApiResult<Nothing>
}

sealed class ApiError {
    data class HttpError(val code: Int, val message: String) : ApiError()
    data class NetworkError(val cause: Throwable) : ApiError()
    data object Unauthorized : ApiError()
    data object Timeout : ApiError()
}
```

### 安全なAPI呼び出し
```kotlin
suspend fun <T> safeApiCall(apiCall: suspend () -> T): ApiResult<T> {
    return try {
        ApiResult.Success(apiCall())
    } catch (e: HttpException) {
        ApiResult.Error(ApiError.HttpError(e.code(), e.message()))
    } catch (e: IOException) {
        ApiResult.Error(ApiError.NetworkError(e))
    }
}
```

### Repository実装パターン
```kotlin
class UserRepositoryImpl @Inject constructor(
    private val apiService: ApiService,
    private val userMapper: UserMapper
) : UserRepository {

    override suspend fun getUser(id: String): Result<User> {
        return safeApiCall { apiService.getUser(id) }
            .map { userMapper.toDomain(it) }
            .toResult()
    }
}
```

## 含まれるセクション

1. **基本構成** - 技術スタック、アーキテクチャ
2. **Retrofit + OkHttp構成** - API Service、OkHttpClient、カスタムInterceptor
3. **エラーハンドリング** - ApiResult型、ApiError sealed class、safeApiCall
4. **Repository層との連携** - 実装パターン、DTO変換、キャッシュ戦略
5. **認証・トークン管理** - TokenProvider、リフレッシュ付きAuthenticator
6. **OpenAPI Generator** - 設定、仕様例、カスタマイズ
7. **テスタビリティ** - MockWebServer、Repositoryテスト、Fake実装
8. **ベストプラクティス** - 設計原則、チェックリスト、アンチパターン

## 詳細ガイドライン

詳細は [REFERENCE.md](./REFERENCE.md) を参照してください。
