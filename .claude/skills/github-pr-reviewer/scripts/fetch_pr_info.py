#!/usr/bin/env python3
"""
GitHub PR情報取得スクリプト

指定されたPRの詳細情報を取得してJSON形式で出力します。
"""

import sys
import json
import argparse
from pathlib import Path

# 同じディレクトリのgithub_api.pyをインポート
sys.path.insert(0, str(Path(__file__).parent))
from github_api import GitHubAPI


def fetch_pr_info(pr_url: str, output_file: str = None) -> dict:
    """
    PR情報を取得

    Args:
        pr_url: PR URL
        output_file: 出力先JSONファイルパス（省略時は標準出力）

    Returns:
        PR情報を含む辞書
    """
    api = GitHubAPI()

    # PR URLをパース
    owner, repo, pr_number = api.parse_pr_url(pr_url)

    print(f"Fetching PR information for {owner}/{repo}#{pr_number}...", file=sys.stderr)

    # PR基本情報を取得
    pr_info = api.get_pull_request(owner, repo, pr_number)

    # 変更されたファイル一覧を取得
    print("Fetching changed files...", file=sys.stderr)
    files = api.get_pr_files(owner, repo, pr_number)

    # コミット一覧を取得
    print("Fetching commits...", file=sys.stderr)
    commits = api.get_pr_commits(owner, repo, pr_number)

    # 既存のレビューを取得
    print("Fetching existing reviews...", file=sys.stderr)
    reviews = api.get_pr_reviews(owner, repo, pr_number)

    # 統合データを作成
    result = {
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "pr_url": pr_url,
        "title": pr_info["title"],
        "body": pr_info["body"],
        "state": pr_info["state"],
        "author": pr_info["user"]["login"],
        "base_branch": pr_info["base"]["ref"],
        "head_branch": pr_info["head"]["ref"],
        "created_at": pr_info["created_at"],
        "updated_at": pr_info["updated_at"],
        "mergeable": pr_info.get("mergeable"),
        "mergeable_state": pr_info.get("mergeable_state"),
        "files": [
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "changes": f["changes"],
                "patch": f.get("patch", ""),
                "blob_url": f.get("blob_url", "")
            }
            for f in files
        ],
        "commits": [
            {
                "sha": c["sha"],
                "message": c["commit"]["message"],
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"]
            }
            for c in commits
        ],
        "existing_reviews": [
            {
                "id": r["id"],
                "user": r["user"]["login"],
                "state": r["state"],
                "body": r.get("body", ""),
                "submitted_at": r.get("submitted_at")
            }
            for r in reviews
        ],
        "stats": {
            "total_files": len(files),
            "total_additions": sum(f["additions"] for f in files),
            "total_deletions": sum(f["deletions"] for f in files),
            "total_commits": len(commits)
        }
    }

    # 出力
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"PR information saved to {output_file}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub PR information and output as JSON"
    )
    parser.add_argument(
        "--pr-url",
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path (default: stdout)"
    )

    args = parser.parse_args()

    try:
        fetch_pr_info(args.pr_url, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
