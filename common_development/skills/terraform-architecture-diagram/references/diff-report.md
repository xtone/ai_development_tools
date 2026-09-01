# 差分レポート生成

再生成時に前回との変更点を `.md` ファイルとして出力する機能。納品資料・レビュー資料として利用可能。

## 目次

1. [差分の基準点](#差分の基準点)
2. [差分解析手順](#差分解析手順)
3. [出力ファイル](#出力ファイル)

---

## 差分の基準点

| 方式 | コマンド例 | 使用場面 |
|------|-----------|---------|
| デフォルト | `git diff main..HEAD -- '*.tf'` | 開発中のレビュー |
| タグ指定 | `git diff v1.2.0..HEAD -- '*.tf'` | リリース時の納品資料 |
| コミット指定 | `git diff abc1234..HEAD -- '*.tf'` | 柔軟な比較 |

ユーザーが基準を指定しない場合はデフォルト（main ブランチとの差分）を使用する。

## 差分解析手順

1. `git diff` で `.tf` ファイルの差分を取得
2. 差分から追加/削除/変更された resource/module ブロックを抽出
3. 接続関係の変更を特定
4. マークダウン形式でレポート生成

## 出力ファイル

ファイル名: `{diagram-name}-diff.md`

```markdown
# アーキテクチャ変更サマリー

- 基準: main ブランチ (commit: abc1234)
- 現在: feature/xxx ブランチ (commit: def5678)
- 生成日: YYYY-MM-DD

## 追加されたリソース

| リソース | タイプ | 配置先 |
|---------|--------|--------|
| cache | aws_elasticache_cluster | Private Subnet |

## 削除されたリソース

| リソース | タイプ | 元の配置先 |
|---------|--------|-----------|
| old_db | aws_db_instance | Private Subnet |

## 変更されたリソース

| リソース | 属性 | 変更前 | 変更後 |
|---------|------|--------|--------|
| api | desired_count | 2 | 4 |

## 追加された接続

- aws_ecs_service.api → aws_elasticache_cluster.cache

## 削除された接続

- aws_ecs_service.api → aws_db_instance.old_db
```
