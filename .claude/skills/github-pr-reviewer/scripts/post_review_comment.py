#!/usr/bin/env python3
"""
PRレビューコメント投稿スクリプト

PRに対してレビューコメントを投稿します（REQUEST_CHANGES）。
Critical問題が見つかった場合に使用します。
"""

import sys
import json
import argparse
from pathlib import Path

# 同じディレクトリのgithub_api.pyをインポート
sys.path.insert(0, str(Path(__file__).parent))
from github_api import GitHubAPI


def post_review_comment(
    pr_url: str,
    comment_type: str = "REQUEST_CHANGES",
    findings_file: str = None,
    custom_comment: str = None
) -> dict:
    """
    PRレビューコメントを投稿

    Args:
        pr_url: PR URL
        comment_type: コメントタイプ (REQUEST_CHANGES, COMMENT)
        findings_file: 分析結果JSONファイルパス
        custom_comment: カスタムコメント

    Returns:
        作成されたレビュー情報
    """
    api = GitHubAPI()

    # PR URLをパース
    owner, repo, pr_number = api.parse_pr_url(pr_url)

    print(f"Posting review comment to {owner}/{repo}#{pr_number}...", file=sys.stderr)

    # 分析結果を読み込み
    findings = None
    if findings_file:
        with open(findings_file, "r", encoding="utf-8") as f:
            findings = json.load(f)

    # コメントを生成
    if custom_comment:
        comment_body = custom_comment
    elif findings:
        comment_body = generate_review_comment(findings, comment_type)
    else:
        comment_body = "レビューコメントを投稿します。"

    # レビューを作成
    try:
        review = api.create_review(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            event=comment_type,
            body=comment_body
        )

        print(f"Successfully posted review comment to PR #{pr_number}", file=sys.stderr)
        return review

    except Exception as e:
        print(f"Failed to post review comment: {e}", file=sys.stderr)
        raise


def generate_review_comment(findings: dict, comment_type: str) -> str:
    """
    分析結果からレビューコメントを生成

    Args:
        findings: 分析結果
        comment_type: コメントタイプ

    Returns:
        レビューコメント
    """
    scores = findings.get("scores", {})
    summary = findings.get("summary", {})
    findings_data = findings.get("findings", {})

    comment_lines = [
        "## PR Review - Changes Requested",
        "",
        "コードレビューの結果、修正が必要な問題が見つかりました。",
        "",
        "### Analysis Results",
        ""
    ]

    # 各カテゴリーのスコア
    categories = {
        "code_quality": "Code Quality",
        "security": "Security",
        "testing": "Testing",
        "performance": "Performance"
    }

    for key, label in categories.items():
        score = scores.get(key, 10)
        emoji = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
        comment_lines.append(f"#### {emoji} {label}: {score}/10")

    comment_lines.append("")

    # Critical問題の詳細
    if findings_data.get("critical"):
        comment_lines.extend([
            "### ❌ Critical Issues (即座に修正が必要)",
            ""
        ])
        for i, issue in enumerate(findings_data["critical"], 1):
            comment_lines.extend([
                f"**{i}. {issue.get('message')}**",
                f"- File: `{issue.get('file', 'N/A')}`",
                f"- Category: {issue.get('category', 'N/A')}",
                f"- Suggestion: {issue.get('suggestion', 'N/A')}",
                ""
            ])

    # Major問題の詳細
    if findings_data.get("major"):
        comment_lines.extend([
            "### ⚠️ Major Issues (優先的に修正を推奨)",
            ""
        ])
        for i, issue in enumerate(findings_data["major"], 1):
            comment_lines.extend([
                f"**{i}. {issue.get('message')}**",
                f"- File: `{issue.get('file', 'N/A')}`",
                f"- Category: {issue.get('category', 'N/A')}",
                f"- Suggestion: {issue.get('suggestion', 'N/A')}",
                ""
            ])

    # Minor問題の詳細
    if findings_data.get("minor"):
        comment_lines.extend([
            "### 📝 Minor Issues (できれば修正を推奨)",
            ""
        ])
        for i, issue in enumerate(findings_data["minor"], 1):
            comment_lines.extend([
                f"**{i}. {issue.get('message')}**",
                f"- File: `{issue.get('file', 'N/A')}`",
                f"- Suggestion: {issue.get('suggestion', 'N/A')}",
                ""
            ])

    # サマリー
    comment_lines.extend([
        "### Summary",
        "",
        f"- Total issues: {summary.get('total_issues', 0)}",
        f"  - Critical: {summary.get('critical_count', 0)}",
        f"  - Major: {summary.get('major_count', 0)}",
        f"  - Minor: {summary.get('minor_count', 0)}",
        ""
    ])

    if findings_data.get("critical"):
        comment_lines.append(
            "Critical問題を修正後、再度レビューをリクエストしてください。"
        )
    else:
        comment_lines.append(
            "Major/Minor問題の修正をお願いします。"
        )

    return "\n".join(comment_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Post review comment to GitHub PR"
    )
    parser.add_argument(
        "--pr-url",
        required=True,
        help="GitHub PR URL"
    )
    parser.add_argument(
        "--comment-type",
        choices=["REQUEST_CHANGES", "COMMENT"],
        default="REQUEST_CHANGES",
        help="Review comment type"
    )
    parser.add_argument(
        "--findings",
        help="Path to analysis findings JSON file"
    )
    parser.add_argument(
        "--comment",
        help="Custom comment text"
    )

    args = parser.parse_args()

    try:
        result = post_review_comment(
            args.pr_url,
            args.comment_type,
            args.findings,
            args.comment
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
