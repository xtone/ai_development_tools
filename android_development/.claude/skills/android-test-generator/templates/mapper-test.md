# Mapper テストテンプレート

Mapperは純粋関数（Entity→DomainModel変換）であり、`runTest` やコルーチン設定は不要。
JUnit Assert を主力に使用。

> **注意**: 依存関係を持つMapper（RemoteConfig参照、他Mapper委譲等）は「依存ありMapperパターン」を参照。

---

## 基本構造（クラスベースMapper）

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

class {ClassName}Test {

    // === テスト対象 ===
    private lateinit var mapper: {ClassName}

    @Before
    fun setUp() {
        mapper = {ClassName}()
    }

    // === 正常系テスト ===

    @Test
    fun `map - 全フィールドが正しく変換されること`() {
        // Given
        val entity = {EntityType}(
            id = "123",
            title = "Test Title",
            description = "Test Description",
            createdAt = "2025-01-01T00:00:00Z",
            status = 1
        )

        // When
        val result = mapper.map(entity)

        // Then
        assertEquals("123", result.id)
        assertEquals("Test Title", result.title)
        assertEquals("Test Description", result.description)
        assertNotNull(result.createdAt)
        assertEquals({StatusEnum}.ACTIVE, result.status)
    }

    @Test
    fun `map - リストが正しく変換されること`() {
        // Given
        val entities = listOf(
            {EntityType}(id = "1", title = "First"),
            {EntityType}(id = "2", title = "Second")
        )

        // When
        val results = mapper.mapList(entities)

        // Then
        assertEquals(2, results.size)
        assertEquals("1", results[0].id)
        assertEquals("2", results[1].id)
    }
}
```

---

## 拡張関数ベースMapper

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class {ClassName}MapperTest {

    @Test
    fun `toXxx - 全フィールドが正しく変換されること`() {
        // Given
        val entity = {EntityType}(
            id = "123",
            title = "Test Title",
            imageUrl = "https://example.com/image.jpg"
        )

        // When
        val result = entity.to{DomainType}()

        // Then
        assertEquals("123", result.id)
        assertEquals("Test Title", result.title)
        assertEquals("https://example.com/image.jpg", result.imageUrl)
    }

    @Test
    fun `toXxx - リスト変換が正しく動作すること`() {
        // Given
        val entities = listOf(
            {EntityType}(id = "1"),
            {EntityType}(id = "2")
        )

        // When
        val results = entities.map { it.to{DomainType}() }

        // Then
        assertEquals(2, results.size)
    }
}
```

---

## null値・デフォルト値変換テスト

```kotlin
@Test
fun `map - nullフィールドがデフォルト値に変換されること`() {
    // Given
    val entity = {EntityType}(
        id = "123",
        title = null,
        description = null,
        imageUrl = null
    )

    // When
    val result = mapper.map(entity)

    // Then
    assertEquals("123", result.id)
    assertEquals("", result.title)           // null → 空文字
    assertNull(result.description)            // null許容フィールド
    assertEquals({DefaultImage}, result.imageUrl)  // null → デフォルト画像
}

@Test
fun `map - 空文字列が正しく変換されること`() {
    // Given
    val entity = {EntityType}(
        id = "",
        title = ""
    )

    // When
    val result = mapper.map(entity)

    // Then
    assertEquals("", result.id)
    assertEquals("", result.title)
}
```

---

## Enum・型変換テスト

```kotlin
@Test
fun `map - ステータスコードがEnumに正しく変換されること`() {
    // Given - When - Then
    assertEquals({StatusEnum}.ACTIVE, mapper.mapStatus(1))
    assertEquals({StatusEnum}.INACTIVE, mapper.mapStatus(0))
    assertEquals({StatusEnum}.UNKNOWN, mapper.mapStatus(-1))
}

@Test
fun `map - 日付文字列がDateオブジェクトに変換されること`() {
    // Given
    val entity = {EntityType}(
        createdAt = "2025-01-15T10:30:00Z"
    )

    // When
    val result = mapper.map(entity)

    // Then
    assertNotNull(result.createdAt)
}

@Test
fun `map - 不正な日付文字列の場合、nullになること`() {
    // Given
    val entity = {EntityType}(
        createdAt = "invalid-date"
    )

    // When
    val result = mapper.map(entity)

    // Then
    assertNull(result.createdAt)
}
```

---

## 同名Entity問題（import aliasing）

Entity名とDomainModel名が同名の場合、import aliasを使用:

```kotlin
import {data_package}.entity.Article as ArticleEntity
import {domain_package}.model.Article as ArticleModel

class ArticleMapperTest {

    @Test
    fun `map - ArticleEntityがArticleModelに変換されること`() {
        // Given
        val entity = ArticleEntity(id = "1", title = "Test")

        // When
        val result = mapper.map(entity)

        // Then - result は ArticleModel 型
        assertEquals("1", result.id)
    }
}
```

---

## 依存ありMapperパターン

RemoteConfig参照・他Mapper委譲・Photo変換等の依存を持つMapperの場合:

```kotlin
@file:Suppress("NonAsciiCharacters", "TestFunctionName")

package {test_package}

import io.mockk.every
import io.mockk.mockk
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

class {ClassName}Test {

    // === 依存関係（モック） ===
    private lateinit var {subMapperName}: {SubMapperType}
    private lateinit var {configName}: {ConfigType}

    // === テスト対象 ===
    private lateinit var mapper: {ClassName}

    @Before
    fun setUp() {
        {subMapperName} = mockk()
        {configName} = mockk()
        mapper = {ClassName}({subMapperName}, {configName})
    }

    @Test
    fun `map - 依存Mapperの結果が正しく統合されること`() {
        // Given
        val input = mockk<{InputType}>(relaxed = true) {
            every { rows } returns listOf(mockk())
        }

        every { {subMapperName}.map(any(), any()) } returns listOf({ExpectedItem}(...))
        every { {configName}.getValue(any()) } returns {ConfigValue}

        // When
        val result = mapper.map(input, 0)

        // Then
        assertNotNull(result)
        assertEquals(1, result.items.size)
    }
}
```

### ネストされた型参照の注意

APIレスポンスモデルで、フィールドの型が別クラスのネスト型を参照しているケースがある:

```kotlin
// GetArticleResponse.rows は GetTimelineResponse.Row を参照
val rows: List<GetTimelineResponse.Row>?  // ← GetArticleResponse.Row ではない！

// テストでの正しいモック
val rows = listOf(mockk<GetTimelineResponse.Row>())  // ✅
val rows = listOf(mockk<GetArticleResponse.Row>())    // ❌ 存在しない型
```

テスト生成時は、フィールドの型定義を必ず確認すること。

---

## 設計ポイント

| 項目 | 純粋関数Mapper | 依存ありMapper |
|------|--------------|---------------|
| runTest | **不要** | **不要**（非suspend） |
| アサーション | JUnit Assert | JUnit Assert |
| Mock | **不要** | MockK（依存をモック） |
| テストパターン | 入力Entity → 出力DomainModel | 入力 + Mock設定 → 出力 |
| 注意点 | エッジケース網羅 | ネスト型・戻り値型の正確な把握 |
| import alias | 同名クラス時に使用 | 同名クラス時に使用 |

---

## 置換プレースホルダー

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{test_package}` | テストパッケージ名 | `jp.co.nttdocomo.dmenunews.data.mapper` |
| `{ClassName}` | Mapperクラス名 | `ArticleMapper` |
| `{EntityType}` | Entity型（API/DB） | `ArticleEntity` |
| `{DomainType}` | ドメインモデル型 | `Article` |
| `{StatusEnum}` | ステータスEnum | `ArticleStatus` |
| `{DefaultImage}` | デフォルト画像URL | `""` |
| `{data_package}` | dataパッケージ | `jp.co.nttdocomo.dmenunews.data` |
| `{domain_package}` | domainパッケージ | `jp.co.nttdocomo.dmenunews.domain` |
