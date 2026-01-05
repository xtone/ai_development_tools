---
name: android-ui-guidelines
description: |
  Jetpack ComposeでUIを実装する時に参照するコーディングガイドライン。
  「Android UI」「Compose」「Jetpack」「画面実装」「UIコンポーネント」「レイアウト」と言われたら使う。
  Android/Kotlin UI実装のベストプラクティス、アンチパターン、実装パターンを提供する。
---

# Android UIコーディングガイドライン

Jetpack ComposeによるUI実装のベストプラクティスを提供するスキルです。

## このスキルが提供するもの

1. **基本原則**: 宣言的UI、単一方向データフロー、状態ホイスティング
2. **Composable設計**: 命名規則、Modifier、コンポーネント分割
3. **State管理**: UiState設計、ViewModel連携、Side Effects
4. **実装パターン**: リスト、フォーム、ナビゲーション、エラー、ローディング
5. **パフォーマンス最適化**: Recomposition防止、LazyList最適化
6. **アンチパターン**: 避けるべき実装パターン
7. **テスタビリティ**: テスト可能な設計

## クイックリファレンス

### Composable関数の基本形

```kotlin
@Composable
fun MyComponent(
    // 1. 必須パラメータ
    data: Data,
    onClick: () -> Unit,
    // 2. オプショナルパラメータ
    enabled: Boolean = true,
    // 3. Modifier（常にデフォルト値）
    modifier: Modifier = Modifier
) {
    // 渡されたmodifierを最上位要素に適用
    Box(modifier = modifier) {
        // 実装
    }
}
```

### UiState設計

```kotlin
sealed interface ScreenUiState {
    data object Loading : ScreenUiState
    data class Success(val data: Data) : ScreenUiState
    data class Error(val message: String) : ScreenUiState
}
```

### LazyColumnの基本

```kotlin
LazyColumn {
    items(
        items = items,
        key = { it.id }  // 必ずkeyを指定
    ) { item ->
        ItemCard(item = item)
    }
}
```

## 詳細ガイドライン

詳細な実装パターンとガイドラインは [REFERENCE.md](REFERENCE.md) を参照してください。

## チェックリスト

### 実装前
- [ ] 再利用可能なコンポーネントか確認
- [ ] 状態ホイスティングを適用できるか確認
- [ ] Modifierパラメータを追加したか

### 実装中
- [ ] keyをLazyListに指定したか
- [ ] 重い処理をrememberでキャッシュしたか
- [ ] 副作用をLaunchedEffect等で適切に処理しているか

### 実装後
- [ ] @Previewが動作するか
- [ ] 不要なRecompositionがないか
- [ ] テストコードを書いたか
