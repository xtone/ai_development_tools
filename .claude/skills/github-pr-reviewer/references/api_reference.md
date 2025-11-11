# GitHub API Reference

GitHub PR Reviewer スキルで使用する GitHub REST API v3 のリファレンスです。

## 認証

すべてのAPIリクエストには Personal Access Token (PAT) が必要です。

```
Authorization: token YOUR_GITHUB_TOKEN
```

## 使用するエンドポイント

### 1. Pull Requests API

#### PR情報の取得
```
GET /repos/{owner}/{repo}/pulls/{pull_number}
```

レスポンス例:
```json
{
  "number": 123,
  "title": "Add new feature",
  "body": "Description of the PR",
  "user": {
    "login": "username"
  },
  "state": "open",
  "base": {
    "ref": "main"
  },
  "head": {
    "ref": "feature-branch"
  },
  "mergeable": true,
  "mergeable_state": "clean"
}
```

#### 変更されたファイルの取得
```
GET /repos/{owner}/{repo}/pulls/{pull_number}/files
```

レスポンス例:
```json
[
  {
    "filename": "src/app.py",
    "status": "modified",
    "additions": 10,
    "deletions": 5,
    "changes": 15,
    "patch": "@@ -1,5 +1,10 @@\n+added line\n-removed line"
  }
]
```

#### PRのコミット一覧取得
```
GET /repos/{owner}/{repo}/pulls/{pull_number}/commits
```

### 2. Reviews API

#### レビュー一覧の取得
```
GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews
```

#### レビューの作成
```
POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews
```

リクエストボディ:
```json
{
  "event": "APPROVE",
  "body": "LGTM! Great work."
}
```

`event` の値:
- `APPROVE`: PRを承認
- `REQUEST_CHANGES`: 変更を要求
- `COMMENT`: コメントのみ

#### 行別コメントの追加
```
POST /repos/{owner}/{repo}/pulls/{pull_number}/comments
```

リクエストボディ:
```json
{
  "body": "Comment text",
  "commit_id": "commit_sha",
  "path": "file/path.py",
  "line": 10
}
```

### 3. Issues API

#### Issueの作成
```
POST /repos/{owner}/{repo}/issues
```

リクエストボディ:
```json
{
  "title": "Issue title",
  "body": "Issue description",
  "assignees": ["username"],
  "labels": ["bug", "priority:high"]
}
```

#### Issueの更新
```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

### 4. Repository Contents API

#### ファイル内容の取得
```
GET /repos/{owner}/{repo}/contents/{path}?ref={branch}
```

レスポンスの `content` フィールドは Base64 エンコードされています。

## レート制限

- 認証済みリクエスト: 5,000リクエスト/時間
- 未認証リクエスト: 60リクエスト/時間

レート制限の確認:
```
GET /rate_limit
```

## エラーハンドリング

### よくあるエラーコード

- `401 Unauthorized`: トークンが無効または期限切れ
- `403 Forbidden`: 権限不足またはレート制限超過
- `404 Not Found`: リソースが存在しない
- `422 Unprocessable Entity`: リクエストボディが不正

### エラーレスポンス例
```json
{
  "message": "Not Found",
  "documentation_url": "https://docs.github.com/rest"
}
```

## ベストプラクティス

### 1. 条件付きリクエスト

ETag を使用してキャッシュを活用:
```
If-None-Match: "etag_value"
```

304 Not Modified レスポンスの場合、キャッシュを使用。

### 2. ページネーション

大量のデータを取得する場合:
```
GET /repos/{owner}/{repo}/pulls/{pull_number}/files?per_page=100&page=2
```

- `per_page`: 1ページあたりの項目数（最大100）
- `page`: ページ番号

レスポンスヘッダーの `Link` で次ページを確認:
```
Link: <https://api.github.com/...?page=3>; rel="next"
```

### 3. タイムアウト設定

長時間実行されるリクエストに対してタイムアウトを設定:
- 接続タイムアウト: 10秒
- 読み取りタイムアウト: 30秒

## セキュリティ

### トークンの保管

- 環境変数 `GITHUB_TOKEN` に保存
- または `~/.github_token` ファイルに保存（パーミッション 600）
- **絶対にコードにハードコードしない**

### 必要なスコープ

プライベートリポジトリの場合:
- `repo` (フルアクセス)

パブリックリポジトリの場合:
- `public_repo`

その他:
- `pull_requests:write` - PRのレビューや承認

## 参考リンク

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [Pull Requests API](https://docs.github.com/en/rest/pulls)
- [Reviews API](https://docs.github.com/en/rest/pulls/reviews)
- [Issues API](https://docs.github.com/en/rest/issues)
