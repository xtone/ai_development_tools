#!/usr/bin/env python3
"""
PR承認スクリプト

PRをApproveし、オプションでコメントを追加します。
"""

import sys
import json
import argparse
from pathlib import Path

# 同じディレクトリのgithub_api.pyをインポート
sys.path.insert(0, str(Path(__file__).parent))
from github_api import GitHubAPI


def approve_pr(pr_url: str, comment: str = None, analysis_file: str = None) -> dict:
    """
    PRをApprove

    Args:
        pr_url: PR URL
        comment: レビューコメント
        analysis_file: 分析結果JSONファイルパス（省略可）

    Returns:
        作成されたレビュー情報
    """
    api = GitHubAPI()

    # PR URLをパース
    owner, repo, pr_number = api.parse_pr_url(pr_url)

    print(f"Approving PR {owner}/{repo}#{pr_number}...", file=sys.stderr)

    # 分析結果がある場合は読み込む
    analysis_result = None
    if analysis_file:
        with open(analysis_file, "r", encoding="utf-8") as f:
            analysis_result = json.load(f)

    # コメントを生成
    if not comment:
        if analysis_result:
            comment = generate_approval_comment(analysis_result)
        else:
            comment = "コードレビューを完了しました。問題は見つかりませんでした。"

    # PRをApprove
    try:
        review = api.create_review(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            event="APPROVE",
            body=comment
        )

        print(f"Successfully approved PR #{pr_number}", file=sys.stderr)
        return review

    except Exception as e:
        print(f"Failed to approve PR: {e}", file=sys.stderr)
        raise


def generate_approval_comment(analysis_result: dict) -> str:
    """
    分析結果から承認コメントを生成

    Args:
        analysis_result: 分析結果

    Returns:
        承認コメント
    """
    scores = analysis_result.get("scores", {})
    summary = analysis_result.get("summary", {})
    recommendation = analysis_result.get("recommendation", "APPROVE")

    # スコアの表示
    comment_lines = [
        "## PR Review Summary",
        "",
        f"**Status**: {get_status_emoji(recommendation)} {get_status_text(recommendation)}",
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
        comment_lines.append(f"#### {label}: {score}/10")

    comment_lines.append("")
    comment_lines.append("### Summary")
    comment_lines.append("")

    if recommendation == "CONDITIONAL_APPROVE":
        comment_lines.extend([
            "条件付きでApproveします。",
            "",
            f"- 検出された問題: {summary.get('total_issues', 0)} 件",
            f"  - Major: {summary.get('major_count', 0)} 件",
            f"  - Minor: {summary.get('minor_count', 0)} 件",
            f"  - Suggestion: {summary.get('suggestion_count', 0)} 件",
            "",
            "改善点はIssueとして起票しましたので、適宜対応をお願いします。"
        ])
    else:
        comment_lines.extend([
            "コードレビューを完了しました。問題は見つかりませんでした。",
            "",
            "全ての観点から良好な品質です。"
        ])

    return "\n".join(comment_lines)


def get_status_emoji(recommendation: str) -> str:
    """推奨アクションに対応する絵文字を返す"""
    emojis = {
        "APPROVE": "✅",
        "CONDITIONAL_APPROVE": "⚠️",
        "REQUEST_CHANGES": "❌"
    }
    return emojis.get(recommendation, "📝")


def get_status_text(recommendation: str) -> str:
    """推奨アクションに対応するテキストを返す"""
    texts = {
        "APPROVE": "Approved",
        "CONDITIONAL_APPROVE": "Approved with suggestions",
        "REQUEST_CHANGES": "Changes requested"
    }
    return texts.get(recommendation, "Reviewed")


def main():
    parser = argparse.ArgumentParser(
        description="Approve GitHub PR with optional comment"
    )
    parser.add_argument(
        "--pr-url",
        required=True,
        help="GitHub PR URL"
    )
    parser.add_argument(
        "--comment",
        help="Review comment (optional)"
    )
    parser.add_argument(
        "--analysis",
        help="Path to analysis result JSON file (optional)"
    )

    args = parser.parse_args()

    try:
        result = approve_pr(args.pr_url, args.comment, args.analysis)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
