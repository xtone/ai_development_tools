#!/usr/bin/env python3
"""
Issue作成スクリプト

分析結果から改善点をIssueとして起票し、PR作成者にアサインします。
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict

# 同じディレクトリのgithub_api.pyをインポート
sys.path.insert(0, str(Path(__file__).parent))
from github_api import GitHubAPI


def create_issues_from_findings(
    pr_url: str,
    findings_file: str,
    assignee: str = None,
    labels: List[str] = None,
    dry_run: bool = False
) -> List[Dict]:
    """
    分析結果からIssueを作成

    Args:
        pr_url: PR URL
        findings_file: 分析結果JSONファイルパス
        assignee: アサインするユーザー名（省略時はPR作成者）
        labels: 追加するラベルのリスト
        dry_run: True の場合、実際には作成せず内容のみ表示

    Returns:
        作成されたIssue情報のリスト
    """
    api = GitHubAPI()

    # PR URLをパース
    owner, repo, pr_number = api.parse_pr_url(pr_url)

    # 分析結果を読み込み
    with open(findings_file, "r", encoding="utf-8") as f:
        findings = json.load(f)

    # アサイン先を決定
    if not assignee:
        assignee = findings.get("author")

    findings_data = findings.get("findings", {})
    created_issues = []

    # Major/Minor問題のみIssue化（Criticalは直接修正を要求）
    issues_to_create = []

    # Major問題
    for finding in findings_data.get("major", []):
        issues_to_create.append({
            "severity": "major",
            "finding": finding
        })

    # Minor問題
    for finding in findings_data.get("minor", []):
        issues_to_create.append({
            "severity": "minor",
            "finding": finding
        })

    # Suggestion
    for finding in findings_data.get("suggestion", []):
        issues_to_create.append({
            "severity": "suggestion",
            "finding": finding
        })

    print(f"Creating {len(issues_to_create)} issues for PR #{pr_number}...", file=sys.stderr)

    for item in issues_to_create:
        severity = item["severity"]
        finding = item["finding"]

        # Issueのタイトルと本文を生成
        title = generate_issue_title(finding, severity)
        body = generate_issue_body(finding, pr_number, pr_url, severity)

        # ラベルを決定
        issue_labels = labels or []
        issue_labels.extend(get_default_labels(severity, finding.get("category")))

        if dry_run:
            print("\n" + "="*80, file=sys.stderr)
            print(f"[DRY RUN] Would create issue:", file=sys.stderr)
            print(f"Title: {title}", file=sys.stderr)
            print(f"Assignee: {assignee}", file=sys.stderr)
            print(f"Labels: {', '.join(issue_labels)}", file=sys.stderr)
            print(f"\nBody:\n{body}", file=sys.stderr)
            print("="*80, file=sys.stderr)
            continue

        try:
            # Issueを作成
            issue = api.create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=body,
                assignees=[assignee] if assignee else None,
                labels=issue_labels
            )

            created_issues.append({
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
                "assignee": assignee,
                "labels": issue_labels
            })

            print(f"Created issue #{issue['number']}: {title}", file=sys.stderr)

        except Exception as e:
            print(f"Failed to create issue for '{title}': {e}", file=sys.stderr)

    return created_issues


def generate_issue_title(finding: Dict, severity: str) -> str:
    """
    Issueのタイトルを生成

    Args:
        finding: 検出結果
        severity: 重要度

    Returns:
        Issueタイトル
    """
    category = finding.get("category", "improvement")
    message = finding.get("message", "Code improvement needed")
    file_name = finding.get("file", "")

    # カテゴリーの絵文字
    category_emoji = {
        "code_quality": "🔧",
        "security": "🔒",
        "testing": "🧪",
        "performance": "⚡"
    }

    emoji = category_emoji.get(category, "📝")

    # ファイル名があれば含める
    if file_name:
        # パスが長い場合はファイル名のみ
        if "/" in file_name:
            file_name = file_name.split("/")[-1]
        return f"{emoji} [{severity.upper()}] {message} ({file_name})"
    else:
        return f"{emoji} [{severity.upper()}] {message}"


def generate_issue_body(finding: Dict, pr_number: int, pr_url: str, severity: str) -> str:
    """
    Issueの本文を生成

    Args:
        finding: 検出結果
        pr_number: PR番号
        pr_url: PR URL
        severity: 重要度

    Returns:
        Issue本文
    """
    category = finding.get("category", "improvement")
    message = finding.get("message", "")
    suggestion = finding.get("suggestion", "")
    file_name = finding.get("file", "N/A")

    body_lines = [
        f"## 概要",
        "",
        f"PR #{pr_number} のレビューで検出された改善点です。",
        "",
        f"**関連PR**: {pr_url}",
        "",
        "## 詳細",
        "",
        f"**カテゴリー**: {category}",
        f"**重要度**: {severity}",
        f"**ファイル**: `{file_name}`",
        "",
        "### 問題",
        "",
        message,
        "",
        "### 推奨される対応",
        "",
        suggestion,
        "",
        "## チェックリスト",
        "",
        "- [ ] 問題を確認",
        "- [ ] 修正を実装",
        "- [ ] テストを追加/更新",
        "- [ ] ドキュメントを更新（必要に応じて）",
        "",
        "---",
        "",
        f"_このIssueは PR #{pr_number} のレビュー時に自動生成されました。_"
    ]

    return "\n".join(body_lines)


def get_default_labels(severity: str, category: str) -> List[str]:
    """
    デフォルトのラベルを取得

    Args:
        severity: 重要度
        category: カテゴリー

    Returns:
        ラベルのリスト
    """
    labels = []

    # 重要度ラベル
    if severity == "major":
        labels.append("priority: high")
    elif severity == "minor":
        labels.append("priority: medium")
    else:
        labels.append("priority: low")

    # カテゴリーラベル
    category_labels = {
        "code_quality": "code-quality",
        "security": "security",
        "testing": "testing",
        "performance": "performance"
    }

    if category in category_labels:
        labels.append(category_labels[category])

    # その他の汎用ラベル
    labels.append("technical-debt")

    return labels


def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub Issues from PR review findings"
    )
    parser.add_argument(
        "--pr-url",
        required=True,
        help="GitHub PR URL"
    )
    parser.add_argument(
        "--findings",
        required=True,
        help="Path to analysis findings JSON file"
    )
    parser.add_argument(
        "--assignee",
        help="User to assign issues to (defaults to PR author)"
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        help="Additional labels to add to issues"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating issues"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path (default: stdout)"
    )

    args = parser.parse_args()

    try:
        created_issues = create_issues_from_findings(
            args.pr_url,
            args.findings,
            args.assignee,
            args.labels,
            args.dry_run
        )

        result = {
            "pr_url": args.pr_url,
            "created_issues": created_issues,
            "total_created": len(created_issues)
        }

        # 出力
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResult saved to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
