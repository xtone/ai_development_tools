# Android APIクライアント実装ガイドライン

## 1. 基本構成

### 1.1 技術スタック

```kotlin
// build.gradle.kts (Module)
dependencies {
    // Retrofit
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-kotlinx-serialization:2.9.0")

    // OkHttp
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Kotlinx Serialization
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.0")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    // テスト
    testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
}
```

### 1.2 アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────┐
│                      UI Layer                           │
│                    (ViewModel)                          │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    Domain Layer                         │
│              (UseCase / Repository Interface)           │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                     Data Layer                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Repository Implementation           │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │               Remote Data Source                 │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │            API Service (Retrofit)          │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │           OkHttpClient + Interceptors      │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Retrofit + OkHttp構成

### 2.1 基本的なAPI Service定義

```kotlin
interface ApiService {

    // GET - クエリパラメータ
    @GET("users")
    suspend fun getUsers(
        @Query("page") page: Int,
        @Query("limit") limit: Int = 20
    ): List<UserDto>

    // GET - パスパラメータ
    @GET("users/{id}")
    suspend fun getUser(
        @Path("id") userId: String
    ): UserDto

    // POST - リクエストボディ
    @POST("users")
    suspend fun createUser(
        @Body request: CreateUserRequest
    ): UserDto

    // PUT - 更新
    @PUT("users/{id}")
    suspend fun updateUser(
        @Path("id") userId: String,
        @Body request: UpdateUserRequest
    ): UserDto

    // DELETE
    @DELETE("users/{id}")
    suspend fun deleteUser(
        @Path("id") userId: String
    ): Unit

    // ヘッダー付きリクエスト
    @GET("protected/resource")
    suspend fun getProtectedResource(
        @Header("Authorization") token: String
    ): ResourceDto

    // Response型でHTTPレスポンス全体を取得
    @GET("users/{id}")
    suspend fun getUserWithResponse(
        @Path("id") userId: String
    ): Response<UserDto>
}
```

### 2.2 OkHttpClient構成

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor,
        loggingInterceptor: HttpLoggingInterceptor
    ): OkHttpClient {
        return OkHttpClient.Builder()
            // タイムアウト設定
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            // インターセプター（順序重要）
            .addInterceptor(authInterceptor)           // アプリケーション層
            .addInterceptor(loggingInterceptor)        // ログ
            .addNetworkInterceptor(CacheInterceptor()) // ネットワーク層
            // リトライ
            .retryOnConnectionFailure(true)
            // 証明書ピンニング（本番環境）
            .certificatePinner(
                CertificatePinner.Builder()
                    .add("api.example.com", "sha256/AAAA...")
                    .build()
            )
            .build()
    }

    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor {
        return HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }
    }
}
```

### 2.3 Retrofit構成

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object ApiModule {

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        json: Json
    ): Retrofit {
        return Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(
                json.asConverterFactory("application/json".toMediaType())
            )
            .build()
    }

    @Provides
    @Singleton
    fun provideJson(): Json {
        return Json {
            ignoreUnknownKeys = true        // 未知のフィールドを無視
            isLenient = true                // 緩いパース
            encodeDefaults = true           // デフォルト値もエンコード
            explicitNulls = false           // nullを明示的に出力しない
            coerceInputValues = true        // 不正な値をデフォルト値に変換
        }
    }

    @Provides
    @Singleton
    fun provideApiService(retrofit: Retrofit): ApiService {
        return retrofit.create(ApiService::class.java)
    }
}
```

### 2.4 カスタムインターセプター

```kotlin
// 認証インターセプター
class AuthInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()

        // 認証不要なエンドポイントはスキップ
        if (originalRequest.url.encodedPath.contains("/public/")) {
            return chain.proceed(originalRequest)
        }

        val token = tokenProvider.getAccessToken()

        val newRequest = originalRequest.newBuilder()
            .header("Authorization", "Bearer $token")
            .header("Content-Type", "application/json")
            .header("Accept", "application/json")
            .build()

        return chain.proceed(newRequest)
    }
}

// リトライインターセプター
class RetryInterceptor(
    private val maxRetries: Int = 3
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        var response: Response? = null
        var exception: IOException? = null

        repeat(maxRetries) { attempt ->
            try {
                response?.close()
                response = chain.proceed(request)

                if (response?.isSuccessful == true) {
                    return response!!
                }

                // リトライ対象のステータスコード
                if (response?.code !in listOf(408, 429, 500, 502, 503, 504)) {
                    return response!!
                }

            } catch (e: IOException) {
                exception = e
            }

            // 指数バックオフ
            if (attempt < maxRetries - 1) {
                val delay = (2.0.pow(attempt) * 1000).toLong()
                Thread.sleep(delay)
            }
        }

        throw exception ?: IOException("Max retries exceeded")
    }
}

// キャッシュインターセプター
class CacheInterceptor : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val response = chain.proceed(request)

        // GETリクエストのみキャッシュ
        if (request.method == "GET") {
            val cacheControl = CacheControl.Builder()
                .maxAge(5, TimeUnit.MINUTES)
                .build()

            return response.newBuilder()
                .header("Cache-Control", cacheControl.toString())
                .build()
        }

        return response
    }
}
```

---

## 3. エラーハンドリング

### 3.1 API Result型の定義

```kotlin
// 汎用的なAPIレスポンス型
sealed interface ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>
    data class Error(val error: ApiError) : ApiResult<Nothing>
}

// APIエラーの分類
sealed class ApiError {
    // HTTPエラー
    data class HttpError(
        val code: Int,
        val message: String,
        val body: String? = null
    ) : ApiError()

    // ネットワークエラー
    data class NetworkError(
        val cause: Throwable
    ) : ApiError()

    // パースエラー
    data class ParseError(
        val cause: Throwable
    ) : ApiError()

    // 認証エラー
    data object Unauthorized : ApiError()

    // タイムアウト
    data object Timeout : ApiError()

    // 不明なエラー
    data class Unknown(
        val cause: Throwable
    ) : ApiError()
}

// エラーメッセージ取得の拡張関数
fun ApiError.toUserMessage(): String {
    return when (this) {
        is ApiError.HttpError -> when (code) {
            400 -> "リクエストが不正です"
            401 -> "認証が必要です"
            403 -> "アクセスが拒否されました"
            404 -> "データが見つかりません"
            429 -> "リクエストが多すぎます。しばらくお待ちください"
            in 500..599 -> "サーバーエラーが発生しました"
            else -> "エラーが発生しました (${code})"
        }
        is ApiError.NetworkError -> "ネットワーク接続を確認してください"
        is ApiError.ParseError -> "データの処理に失敗しました"
        is ApiError.Unauthorized -> "再度ログインしてください"
        is ApiError.Timeout -> "接続がタイムアウトしました"
        is ApiError.Unknown -> "不明なエラーが発生しました"
    }
}
```

### 3.2 安全なAPI呼び出しラッパー

```kotlin
// API呼び出しをラップするユーティリティ
suspend fun <T> safeApiCall(
    apiCall: suspend () -> T
): ApiResult<T> {
    return try {
        ApiResult.Success(apiCall())
    } catch (e: HttpException) {
        val error = when (e.code()) {
            401 -> ApiError.Unauthorized
            else -> ApiError.HttpError(
                code = e.code(),
                message = e.message(),
                body = e.response()?.errorBody()?.string()
            )
        }
        ApiResult.Error(error)
    } catch (e: SocketTimeoutException) {
        ApiResult.Error(ApiError.Timeout)
    } catch (e: UnknownHostException) {
        ApiResult.Error(ApiError.NetworkError(e))
    } catch (e: IOException) {
        ApiResult.Error(ApiError.NetworkError(e))
    } catch (e: SerializationException) {
        ApiResult.Error(ApiError.ParseError(e))
    } catch (e: Exception) {
        ApiResult.Error(ApiError.Unknown(e))
    }
}

// Responseを含む呼び出し用
suspend fun <T> safeApiCallWithResponse(
    apiCall: suspend () -> Response<T>
): ApiResult<T> {
    return try {
        val response = apiCall()
        if (response.isSuccessful) {
            response.body()?.let {
                ApiResult.Success(it)
            } ?: ApiResult.Error(ApiError.ParseError(NullPointerException("Response body is null")))
        } else {
            val error = when (response.code()) {
                401 -> ApiError.Unauthorized
                else -> ApiError.HttpError(
                    code = response.code(),
                    message = response.message(),
                    body = response.errorBody()?.string()
                )
            }
            ApiResult.Error(error)
        }
    } catch (e: Exception) {
        // 上記と同様のエラーハンドリング
        ApiResult.Error(ApiError.Unknown(e))
    }
}
```

### 3.3 Result型との連携

```kotlin
// ApiResultをKotlin Result型に変換
fun <T> ApiResult<T>.toResult(): Result<T> {
    return when (this) {
        is ApiResult.Success -> Result.success(data)
        is ApiResult.Error -> Result.failure(error.toException())
    }
}

// ApiErrorをExceptionに変換
fun ApiError.toException(): Exception {
    return when (this) {
        is ApiError.HttpError -> HttpException(code, message)
        is ApiError.NetworkError -> NetworkException(cause)
        is ApiError.ParseError -> ParseException(cause)
        is ApiError.Unauthorized -> UnauthorizedException()
        is ApiError.Timeout -> TimeoutException()
        is ApiError.Unknown -> cause as? Exception ?: RuntimeException(cause)
    }
}

// カスタム例外クラス
class HttpException(val code: Int, override val message: String) : Exception(message)
class NetworkException(cause: Throwable) : Exception(cause)
class ParseException(cause: Throwable) : Exception(cause)
class UnauthorizedException : Exception("Unauthorized")
class TimeoutException : Exception("Timeout")
```

---

## 4. Repository層との連携

### 4.1 Repository実装パターン

```kotlin
// Domain層のインターフェース
interface UserRepository {
    suspend fun getUsers(page: Int): Result<List<User>>
    suspend fun getUser(id: String): Result<User>
    suspend fun createUser(name: String, email: String): Result<User>
    fun observeUsers(): Flow<List<User>>
}

// Data層の実装
class UserRepositoryImpl @Inject constructor(
    private val apiService: ApiService,
    private val userDao: UserDao,
    private val userMapper: UserMapper
) : UserRepository {

    override suspend fun getUsers(page: Int): Result<List<User>> {
        return safeApiCall {
            apiService.getUsers(page = page)
        }.map { dtos ->
            dtos.map { userMapper.toDomain(it) }
        }.toResult()
    }

    override suspend fun getUser(id: String): Result<User> {
        return safeApiCall {
            apiService.getUser(userId = id)
        }.map { dto ->
            userMapper.toDomain(dto)
        }.toResult()
    }

    override suspend fun createUser(name: String, email: String): Result<User> {
        return safeApiCall {
            apiService.createUser(
                request = CreateUserRequest(name = name, email = email)
            )
        }.map { dto ->
            userMapper.toDomain(dto)
        }.toResult()
    }

    override fun observeUsers(): Flow<List<User>> {
        return userDao.observeAll()
            .map { entities -> entities.map { userMapper.entityToDomain(it) } }
    }
}

// ApiResult用の拡張関数
inline fun <T, R> ApiResult<T>.map(transform: (T) -> R): ApiResult<R> {
    return when (this) {
        is ApiResult.Success -> ApiResult.Success(transform(data))
        is ApiResult.Error -> this
    }
}
```

### 4.2 DTOとドメインモデルの変換

```kotlin
// DTO（Data Transfer Object）
@Serializable
data class UserDto(
    val id: String,
    val name: String,
    val email: String,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("avatar_url")
    val avatarUrl: String? = null,
    val status: String = "active"
)

// ドメインモデル
data class User(
    val id: UserId,
    val name: String,
    val email: Email,
    val createdAt: Instant,
    val avatarUrl: String?,
    val status: UserStatus
)

@JvmInline
value class UserId(val value: String)

@JvmInline
value class Email(val value: String)

enum class UserStatus {
    ACTIVE, INACTIVE, SUSPENDED
}

// Mapper
class UserMapper @Inject constructor() {

    fun toDomain(dto: UserDto): User {
        return User(
            id = UserId(dto.id),
            name = dto.name,
            email = Email(dto.email),
            createdAt = Instant.parse(dto.createdAt),
            avatarUrl = dto.avatarUrl,
            status = parseStatus(dto.status)
        )
    }

    fun toDto(domain: User): UserDto {
        return UserDto(
            id = domain.id.value,
            name = domain.name,
            email = domain.email.value,
            createdAt = domain.createdAt.toString(),
            avatarUrl = domain.avatarUrl,
            status = domain.status.name.lowercase()
        )
    }

    private fun parseStatus(status: String): UserStatus {
        return when (status.lowercase()) {
            "active" -> UserStatus.ACTIVE
            "inactive" -> UserStatus.INACTIVE
            "suspended" -> UserStatus.SUSPENDED
            else -> UserStatus.ACTIVE
        }
    }
}
```

### 4.3 キャッシュ戦略

```kotlin
// キャッシュ付きRepository
class CachedUserRepository @Inject constructor(
    private val apiService: ApiService,
    private val userDao: UserDao,
    private val userMapper: UserMapper,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) : UserRepository {

    // Network First戦略
    override suspend fun getUsers(page: Int): Result<List<User>> = withContext(ioDispatcher) {
        // まずAPIから取得を試みる
        val apiResult = safeApiCall { apiService.getUsers(page = page) }

        when (apiResult) {
            is ApiResult.Success -> {
                // 成功したらキャッシュを更新
                val entities = apiResult.data.map { userMapper.toEntity(it) }
                userDao.insertAll(entities)
                Result.success(apiResult.data.map { userMapper.toDomain(it) })
            }
            is ApiResult.Error -> {
                // 失敗したらキャッシュから取得
                val cached = userDao.getAll()
                if (cached.isNotEmpty()) {
                    Result.success(cached.map { userMapper.entityToDomain(it) })
                } else {
                    apiResult.toResult()
                }
            }
        }
    }

    // Cache First戦略
    suspend fun getUsersCacheFirst(page: Int): Flow<Result<List<User>>> = flow {
        // まずキャッシュを返す
        val cached = userDao.getAll()
        if (cached.isNotEmpty()) {
            emit(Result.success(cached.map { userMapper.entityToDomain(it) }))
        }

        // バックグラウンドでAPIから取得
        val apiResult = safeApiCall { apiService.getUsers(page = page) }
        when (apiResult) {
            is ApiResult.Success -> {
                val entities = apiResult.data.map { userMapper.toEntity(it) }
                userDao.insertAll(entities)
                emit(Result.success(apiResult.data.map { userMapper.toDomain(it) }))
            }
            is ApiResult.Error -> {
                if (cached.isEmpty()) {
                    emit(apiResult.toResult())
                }
            }
        }
    }.flowOn(ioDispatcher)

    // Stale-While-Revalidate戦略
    fun getUsersStaleWhileRevalidate(): Flow<List<User>> {
        return userDao.observeAll()
            .onStart {
                // 購読開始時にAPIから最新データを取得
                refreshUsers()
            }
            .map { entities -> entities.map { userMapper.entityToDomain(it) } }
    }

    private suspend fun refreshUsers() {
        safeApiCall { apiService.getUsers(page = 1) }
            .onSuccess { dtos ->
                val entities = dtos.map { userMapper.toEntity(it) }
                userDao.insertAll(entities)
            }
    }
}

// ApiResult用の拡張関数
inline fun <T> ApiResult<T>.onSuccess(action: (T) -> Unit): ApiResult<T> {
    if (this is ApiResult.Success) {
        action(data)
    }
    return this
}
```

---

## 5. 認証・トークン管理

### 5.1 トークン管理

```kotlin
interface TokenProvider {
    fun getAccessToken(): String?
    fun getRefreshToken(): String?
    suspend fun refreshAccessToken(): Result<String>
    fun clearTokens()
}

class TokenProviderImpl @Inject constructor(
    private val encryptedPrefs: EncryptedSharedPreferences
) : TokenProvider {

    private companion object {
        const val KEY_ACCESS_TOKEN = "access_token"
        const val KEY_REFRESH_TOKEN = "refresh_token"
        const val KEY_TOKEN_EXPIRY = "token_expiry"
    }

    override fun getAccessToken(): String? {
        return encryptedPrefs.getString(KEY_ACCESS_TOKEN, null)
    }

    override fun getRefreshToken(): String? {
        return encryptedPrefs.getString(KEY_REFRESH_TOKEN, null)
    }

    fun saveTokens(accessToken: String, refreshToken: String, expiresIn: Long) {
        encryptedPrefs.edit {
            putString(KEY_ACCESS_TOKEN, accessToken)
            putString(KEY_REFRESH_TOKEN, refreshToken)
            putLong(KEY_TOKEN_EXPIRY, System.currentTimeMillis() + expiresIn * 1000)
        }
    }

    fun isTokenExpired(): Boolean {
        val expiry = encryptedPrefs.getLong(KEY_TOKEN_EXPIRY, 0)
        return System.currentTimeMillis() >= expiry - 60_000 // 1分前に期限切れとみなす
    }

    override suspend fun refreshAccessToken(): Result<String> {
        // 実装はAuthRepositoryに委譲
        return Result.failure(NotImplementedError())
    }

    override fun clearTokens() {
        encryptedPrefs.edit {
            remove(KEY_ACCESS_TOKEN)
            remove(KEY_REFRESH_TOKEN)
            remove(KEY_TOKEN_EXPIRY)
        }
    }
}
```

### 5.2 トークンリフレッシュ付きインターセプター

```kotlin
class AuthenticatorInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider,
    private val authApi: Lazy<AuthApi>  // 循環依存回避のためLazy
) : Authenticator {

    private val mutex = Mutex()

    override fun authenticate(route: Route?, response: Response): Request? {
        // 401以外は処理しない
        if (response.code != 401) return null

        // 既にリトライ済みの場合は諦める
        if (response.request.header("X-Retry") != null) {
            return null
        }

        return runBlocking {
            mutex.withLock {
                // 他のリクエストで既にリフレッシュ済みかチェック
                val currentToken = tokenProvider.getAccessToken()
                val requestToken = response.request.header("Authorization")
                    ?.removePrefix("Bearer ")

                if (currentToken != null && currentToken != requestToken) {
                    // 既に新しいトークンがある
                    return@runBlocking retryRequest(response.request, currentToken)
                }

                // トークンをリフレッシュ
                val refreshToken = tokenProvider.getRefreshToken()
                if (refreshToken == null) {
                    // リフレッシュトークンがない場合はログアウト
                    tokenProvider.clearTokens()
                    return@runBlocking null
                }

                try {
                    val result = authApi.get().refreshToken(
                        RefreshTokenRequest(refreshToken = refreshToken)
                    )
                    tokenProvider.saveTokens(
                        accessToken = result.accessToken,
                        refreshToken = result.refreshToken,
                        expiresIn = result.expiresIn
                    )
                    retryRequest(response.request, result.accessToken)
                } catch (e: Exception) {
                    tokenProvider.clearTokens()
                    null
                }
            }
        }
    }

    private fun retryRequest(request: Request, token: String): Request {
        return request.newBuilder()
            .header("Authorization", "Bearer $token")
            .header("X-Retry", "true")
            .build()
    }
}
```

---

## 6. OpenAPI Generator

### 6.1 基本設定

```kotlin
// build.gradle.kts
plugins {
    id("org.openapi.generator") version "7.2.0"
}

openApiGenerate {
    generatorName.set("kotlin")
    inputSpec.set("$projectDir/specs/api.yaml")
    outputDir.set("$buildDir/generated/openapi")

    apiPackage.set("com.example.api.generated")
    modelPackage.set("com.example.api.generated.model")

    configOptions.set(mapOf(
        "library" to "jvm-retrofit2",
        "useCoroutines" to "true",
        "serializationLibrary" to "kotlinx_serialization",
        "dateLibrary" to "java8",
        "enumPropertyNaming" to "UPPERCASE",
        "generateApiTests" to "false",
        "generateModelTests" to "false"
    ))

    // 特定のAPIのみ生成
    // apisToGenerate.set("UsersApi,ArticlesApi")

    // 特定のモデルのみ生成
    // modelsToGenerate.set("User,Article")
}

// ソースセットに追加
sourceSets {
    main {
        kotlin {
            srcDir("$buildDir/generated/openapi/src/main/kotlin")
        }
    }
}

tasks.named("compileKotlin") {
    dependsOn("openApiGenerate")
}
```

### 6.2 OpenAPI仕様の例

```yaml
# api.yaml
openapi: 3.0.3
info:
  title: Sample API
  version: 1.0.0

servers:
  - url: https://api.example.com/v1

paths:
  /users:
    get:
      operationId: getUsers
      summary: Get all users
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      operationId: createUser
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

  /users/{id}:
    get:
      operationId: getUser
      summary: Get a user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: Not found

components:
  schemas:
    User:
      type: object
      required:
        - id
        - name
        - email
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time
        avatarUrl:
          type: string
          nullable: true

    CreateUserRequest:
      type: object
      required:
        - name
        - email
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 100
        email:
          type: string
          format: email

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer

security:
  - bearerAuth: []
```

### 6.3 生成コードのカスタマイズ

```kotlin
// カスタムテンプレートの使用
openApiGenerate {
    templateDir.set("$projectDir/openapi-templates")
}

// Mustacheテンプレート例 (api.mustache)
{{#operations}}
interface {{classname}} {
    {{#operation}}
    /**
     * {{summary}}
     * {{notes}}
     */
    @{{httpMethod}}("{{path}}")
    suspend fun {{operationId}}(
        {{#allParams}}
        @{{#isPathParam}}Path{{/isPathParam}}{{#isQueryParam}}Query{{/isQueryParam}}{{#isBodyParam}}Body{{/isBodyParam}}("{{baseName}}") {{paramName}}: {{dataType}}{{^required}} = {{#defaultValue}}{{defaultValue}}{{/defaultValue}}{{^defaultValue}}null{{/defaultValue}}{{/required}}{{^-last}},{{/-last}}
        {{/allParams}}
    ): {{#returnType}}{{returnType}}{{/returnType}}{{^returnType}}Unit{{/returnType}}

    {{/operation}}
}
{{/operations}}
```

### 6.4 手動実装との使い分け

```kotlin
// 生成コードをラップするアダプター
class UserApiAdapter @Inject constructor(
    private val generatedApi: GeneratedUsersApi  // OpenAPI Generator生成
) {

    // 生成されたAPIをラップして、プロジェクト固有の処理を追加
    suspend fun getUsers(page: Int): ApiResult<List<UserDto>> {
        return safeApiCall {
            generatedApi.getUsers(page = page, limit = 20)
        }
    }

    // 生成コードにない追加のエンドポイント（手動実装）
    suspend fun searchUsers(query: String): ApiResult<List<UserDto>> {
        // カスタム実装
        return safeApiCall {
            // ...
        }
    }
}
```

**使い分けの指針:**

| ケース | 推奨 |
|-------|-----|
| 標準的なCRUD操作 | OpenAPI Generator |
| 複雑なリクエスト/レスポンス | 手動実装 |
| 頻繁に変更されるAPI | OpenAPI Generator |
| 特殊な認証フロー | 手動実装 |
| マルチパートアップロード | 手動実装 |
| WebSocket | 手動実装 |

---

## 7. テスタビリティ

### 7.1 MockWebServer

```kotlin
class UserApiTest {

    private lateinit var mockWebServer: MockWebServer
    private lateinit var apiService: ApiService

    @Before
    fun setup() {
        mockWebServer = MockWebServer()
        mockWebServer.start()

        val retrofit = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .client(OkHttpClient.Builder().build())
            .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
            .build()

        apiService = retrofit.create(ApiService::class.java)
    }

    @After
    fun teardown() {
        mockWebServer.shutdown()
    }

    @Test
    fun `getUsers returns list of users`() = runTest {
        // Given
        val responseBody = """
            [
                {"id": "1", "name": "Alice", "email": "alice@example.com"},
                {"id": "2", "name": "Bob", "email": "bob@example.com"}
            ]
        """.trimIndent()

        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody(responseBody)
                .setHeader("Content-Type", "application/json")
        )

        // When
        val result = apiService.getUsers(page = 1)

        // Then
        assertThat(result).hasSize(2)
        assertThat(result[0].name).isEqualTo("Alice")

        // リクエストの検証
        val request = mockWebServer.takeRequest()
        assertThat(request.path).isEqualTo("/users?page=1&limit=20")
        assertThat(request.method).isEqualTo("GET")
    }

    @Test
    fun `getUser returns 404 error`() = runTest {
        // Given
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(404)
                .setBody("""{"error": "User not found"}""")
        )

        // When & Then
        val exception = assertThrows<HttpException> {
            apiService.getUser(userId = "999")
        }
        assertThat(exception.code()).isEqualTo(404)
    }

    @Test
    fun `handles network timeout`() = runTest {
        // Given
        mockWebServer.enqueue(
            MockResponse()
                .setSocketPolicy(SocketPolicy.NO_RESPONSE)
        )

        val clientWithTimeout = OkHttpClient.Builder()
            .readTimeout(1, TimeUnit.SECONDS)
            .build()

        val apiWithTimeout = Retrofit.Builder()
            .baseUrl(mockWebServer.url("/"))
            .client(clientWithTimeout)
            .addConverterFactory(Json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ApiService::class.java)

        // When & Then
        assertThrows<SocketTimeoutException> {
            apiWithTimeout.getUsers(page = 1)
        }
    }
}
```

### 7.2 Repositoryテスト

```kotlin
class UserRepositoryImplTest {

    private lateinit var repository: UserRepositoryImpl
    private val apiService: ApiService = mockk()
    private val userDao: UserDao = mockk(relaxed = true)
    private val userMapper = UserMapper()

    @Before
    fun setup() {
        repository = UserRepositoryImpl(
            apiService = apiService,
            userDao = userDao,
            userMapper = userMapper
        )
    }

    @Test
    fun `getUsers returns success when api call succeeds`() = runTest {
        // Given
        val userDtos = listOf(
            UserDto(id = "1", name = "Alice", email = "alice@example.com", createdAt = "2024-01-01T00:00:00Z"),
            UserDto(id = "2", name = "Bob", email = "bob@example.com", createdAt = "2024-01-02T00:00:00Z")
        )
        coEvery { apiService.getUsers(page = 1) } returns userDtos

        // When
        val result = repository.getUsers(page = 1)

        // Then
        assertThat(result.isSuccess).isTrue()
        assertThat(result.getOrNull()).hasSize(2)
        assertThat(result.getOrNull()?.first()?.name).isEqualTo("Alice")
    }

    @Test
    fun `getUsers returns failure when api call fails`() = runTest {
        // Given
        coEvery { apiService.getUsers(page = 1) } throws HttpException(
            Response.error<List<UserDto>>(
                500,
                "Server Error".toResponseBody()
            )
        )

        // When
        val result = repository.getUsers(page = 1)

        // Then
        assertThat(result.isFailure).isTrue()
    }

    @Test
    fun `getUsers returns cached data when api fails and cache exists`() = runTest {
        // Given
        val cachedEntities = listOf(
            UserEntity(id = "1", name = "Cached", email = "cached@example.com", createdAt = 0L)
        )
        coEvery { apiService.getUsers(page = 1) } throws IOException("Network error")
        coEvery { userDao.getAll() } returns cachedEntities

        // When
        val result = repository.getUsers(page = 1)

        // Then
        assertThat(result.isSuccess).isTrue()
        assertThat(result.getOrNull()?.first()?.name).isEqualTo("Cached")
    }
}
```

### 7.3 テストダブルの活用

```kotlin
// Fake実装
class FakeApiService : ApiService {

    private val users = mutableListOf<UserDto>()
    var shouldFail = false
    var failureException: Exception = IOException("Network error")

    override suspend fun getUsers(page: Int, limit: Int): List<UserDto> {
        if (shouldFail) throw failureException
        return users.drop((page - 1) * limit).take(limit)
    }

    override suspend fun getUser(userId: String): UserDto {
        if (shouldFail) throw failureException
        return users.find { it.id == userId }
            ?: throw HttpException(Response.error<UserDto>(404, "".toResponseBody()))
    }

    override suspend fun createUser(request: CreateUserRequest): UserDto {
        if (shouldFail) throw failureException
        val newUser = UserDto(
            id = UUID.randomUUID().toString(),
            name = request.name,
            email = request.email,
            createdAt = Instant.now().toString()
        )
        users.add(newUser)
        return newUser
    }

    // テスト用ヘルパー
    fun addUser(user: UserDto) {
        users.add(user)
    }

    fun clear() {
        users.clear()
    }
}

// テストでの使用
class UserRepositoryIntegrationTest {

    private val fakeApiService = FakeApiService()
    private lateinit var repository: UserRepository

    @Before
    fun setup() {
        repository = UserRepositoryImpl(
            apiService = fakeApiService,
            userDao = FakeUserDao(),
            userMapper = UserMapper()
        )
    }

    @Test
    fun `complete user flow`() = runTest {
        // Create
        val createResult = repository.createUser("Alice", "alice@example.com")
        assertThat(createResult.isSuccess).isTrue()

        val createdUser = createResult.getOrThrow()

        // Read
        val getResult = repository.getUser(createdUser.id.value)
        assertThat(getResult.isSuccess).isTrue()
        assertThat(getResult.getOrThrow().name).isEqualTo("Alice")

        // List
        val listResult = repository.getUsers(page = 1)
        assertThat(listResult.getOrThrow()).hasSize(1)
    }
}
```

---

## 8. ベストプラクティスまとめ

### 8.1 設計原則

| 原則 | 説明 |
|-----|------|
| 単一責任 | API Service、Repository、Mapperは単一の責務を持つ |
| 依存性逆転 | Domain層はインターフェースに依存、Data層が実装 |
| 早期失敗 | エラーは早期にキャッチし、適切な型で伝播 |
| イミュータブル | DTOとドメインモデルはdata classで不変に |

### 8.2 チェックリスト

**実装前**
- [ ] OpenAPI仕様が存在するか確認
- [ ] 認証方式を確認
- [ ] エラーレスポンスの形式を確認

**実装中**
- [ ] Retrofitインターフェースは suspend 関数
- [ ] Result型またはsealed classでエラーをラップ
- [ ] DTOとドメインモデルを分離
- [ ] Mapperを実装

**実装後**
- [ ] MockWebServerでAPIテストを作成
- [ ] Repositoryのテストを作成
- [ ] エラーケースのテストを追加

### 8.3 アンチパターン

```kotlin
// ❌ 生のAPIレスポンスをUI層に渡す
class BadViewModel : ViewModel() {
    fun loadUser() {
        viewModelScope.launch {
            val user = apiService.getUser("1")  // DTOをそのまま使用
            _uiState.value = user
        }
    }
}

// ✅ Repository経由でドメインモデルを取得
class GoodViewModel(
    private val userRepository: UserRepository
) : ViewModel() {
    fun loadUser() {
        viewModelScope.launch {
            userRepository.getUser("1")
                .onSuccess { user -> _uiState.value = UiState.Success(user) }
                .onFailure { error -> _uiState.value = UiState.Error(error.message) }
        }
    }
}

// ❌ 例外を握りつぶす
suspend fun badApiCall(): User? {
    return try {
        apiService.getUser("1").toDomain()
    } catch (e: Exception) {
        null  // エラー情報が失われる
    }
}

// ✅ Result型でエラーを伝播
suspend fun goodApiCall(): Result<User> {
    return safeApiCall { apiService.getUser("1") }
        .map { it.toDomain() }
        .toResult()
}
```

---

## 9. 参考リンク

- [Retrofit公式ドキュメント](https://square.github.io/retrofit/)
- [OkHttp公式ドキュメント](https://square.github.io/okhttp/)
- [Kotlinx Serialization](https://github.com/Kotlin/kotlinx.serialization)
- [OpenAPI Generator](https://openapi-generator.tech/)
- [Android Developers - Network](https://developer.android.com/training/basics/network-ops)
