# プロジェクト固有のテストパターン（テンプレート）

**Project**: [your-android-project]
**Last Updated**: [YYYY-MM-DD]

このドキュメントは、プロジェクト固有のテスト実行方法、失敗パターン、ベストプラクティスをまとめるためのテンプレートです。

**使い方**: このファイルをコピーして `project-specific.md` として保存し、プロジェクトの実態に合わせて記入してください。

---

## 📋 プロジェクト構成

### ビルドバリアント

プロジェクトのビルドバリアントを記入してください：

| Variant | Purpose | 用途 |
|---------|---------|------|
| `variant1` | 説明 | 用途 |
| `variant2` | 説明 | 用途 |
| `variant3` | 説明 | 用途 |

### モジュール構成

```
your-project/
├── app/              # 説明
├── module1/          # 説明
├── module2/          # 説明
└── common/           # 説明
```

**依存関係**:
```
app → module1 → module2
     ↓
  common
```

---

## 🚀 テスト実行方法

### 標準的な実行方法（推奨）

#### 単一バリアント・単一モジュール（最速）

```bash
# JAVA_HOME設定 + テスト実行
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :module:testVariantDebugUnitTest
```

**使用ケース**:
- 特定モジュールの動作確認
- 開発中の頻繁なテスト実行

#### 全バリアント・単一モジュール（CI相当、推奨）

```bash
# CI環境と同等のテスト
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :module:test
```

**使用ケース**:
- コミット前の最終確認
- CI失敗の予防

---

## ❌ よくあるエラーと対処法

### Error 1: `Unknown command-line option '--tests'`

**エラーメッセージ**:
```
Problem configuring task :module:test from command line.
> Unknown command-line option '--tests'.
```

**原因**:
- 複数のビルドバリアントが存在するため、`--tests` フラグが使用不可

**対処法**:
```bash
# ✅ 正しい
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :module:testVariantDebugUnitTest
```

### Error 2: `Unable to locate a Java Runtime`

**エラーメッセージ**:
```
The operation couldn't be completed. Unable to locate a Java Runtime.
```

**原因**:
- JAVA_HOME環境変数が未設定

**対処法**:
```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
./gradlew :module:testVariantDebugUnitTest
```

---

## 🧪 テスト標準パターン

### アサーションライブラリ

プロジェクトで使用しているアサーションライブラリを記入：

**例**: Google Truth, JUnit assertions, AssertJ 等

```kotlin
import com.google.common.truth.Truth.assertThat

// 基本的なアサーション
assertThat(actual).isEqualTo(expected)
assertThat(value).isNull()
assertThat(list).hasSize(10)
```

### プロジェクト固有のパターン

#### パターン1: [パターン名]

**実装例**:
```kotlin
// プロジェクト固有の実装パターンを記入
```

**テスト例**:
```kotlin
@Test
fun `テスト名`() {
    // Given

    // When

    // Then
    assertThat(result).isEqualTo(expected)
}
```

---

## 🔄 CI/CD統合

### ローカル環境とCIの差異

| 項目 | ローカル環境 | CI |
|------|------------|----|
| テストバリアント | 通常1バリアント | 全バリアント |
| JAVA_HOME | 未設定の場合あり | 自動設定済み |
| 実行時間 | 選択的実行可能 | 全テスト実行 |

### CI失敗の予防策

```bash
# ✅ 推奨: コミット前にCI相当のテスト実行
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew test

# すべて成功することを確認
# ✅ BUILD SUCCESSFUL

# 安全にコミット
git add . && git commit -m "feat: 新機能追加" && git push
```

---

## 📊 テスト実行の推奨フロー

### 開発中（頻繁な実行）

```bash
# 1. 単一モジュール・単一バリアント（最速）
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew :module:testVariantDebugUnitTest
```

### コミット前（必須）

```bash
# 2. 全バリアント確認（CI相当）
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" && \
./gradlew test

# ✅ BUILD SUCCESSFUL 確認後にコミット
git add . && git commit -m "fix: バグ修正" && git push
```

---

## 🎯 ベストプラクティス

### ✅ DO

1. **JAVA_HOME を常に設定**
2. **コミット前に全バリアント確認**
3. **プロジェクト標準のライブラリを使用**

### ❌ DON'T

1. **単一バリアントのみ確認してコミットしない**
2. **JAVA_HOME未設定で実行しない**

---

## 📚 関連ドキュメント

- [test-failure-patterns.md](./test-failure-patterns.md) - 一般的なテスト失敗パターン
- `~/.config/claude-code/AI_DEVELOPMENT_GUIDELINES.md` - AI開発全般のガイドライン

---

**Version**: v1.0
**Last Updated**: [YYYY-MM-DD]
**Maintainer**: [Your Name]
