#!/usr/bin/env python3
"""
PR分析スクリプト

PR情報を分析して、コード品質、セキュリティ、テスト、パフォーマンスの観点から
問題点や改善点を抽出します。

このスクリプトは分析ロジックの骨組みを提供します。
実際の分析はClaude AIによって実行され、このスクリプトはその結果を構造化します。
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List


# セキュリティパターン（簡易版）
SECURITY_PATTERNS = {
    "hardcoded_secrets": [
        r"password\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
        r"secret\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]+['\"]",
    ],
    "sql_injection": [
        r"execute\s*\([^)]*\+[^)]*\)",
        r"SELECT.*FROM.*WHERE.*\+",
    ],
    "xss_vulnerability": [
        r"innerHTML\s*=",
        r"dangerouslySetInnerHTML",
    ],
    "insecure_random": [
        r"Math\.random\(\)",
        r"Random\(\)",
    ]
}

# パフォーマンスパターン
PERFORMANCE_PATTERNS = {
    "n_plus_one": [
        r"for\s+.*:\s*\n\s*.*\.get\(",
        r"for\s+.*:\s*\n\s*.*\.query\(",
    ],
    "inefficient_loop": [
        r"for\s+.*:\s*\n\s*for\s+.*:\s*\n\s*for\s+",  # Triple nested loops
    ]
}


def analyze_code_quality(files: List[Dict]) -> List[Dict]:
    """
    コード品質を分析

    Args:
        files: 変更されたファイルのリスト

    Returns:
        問題点のリスト
    """
    issues = []

    for file_info in files:
        filename = file_info["filename"]
        patch = file_info.get("patch", "")

        # ファイルサイズチェック
        if file_info["changes"] > 500:
            issues.append({
                "severity": "minor",
                "category": "code_quality",
                "file": filename,
                "message": f"ファイルの変更が大きすぎます ({file_info['changes']} 行)",
                "suggestion": "大きな変更は複数のPRに分割することを検討してください"
            })

        # 長い行のチェック
        for line in patch.split("\n"):
            if line.startswith("+") and len(line) > 120:
                issues.append({
                    "severity": "suggestion",
                    "category": "code_quality",
                    "file": filename,
                    "message": "120文字を超える長い行があります",
                    "suggestion": "可読性のため、行を分割することを検討してください"
                })
                break

        # TODOコメントのチェック
        if re.search(r"TODO|FIXME|XXX", patch, re.IGNORECASE):
            issues.append({
                "severity": "minor",
                "category": "code_quality",
                "file": filename,
                "message": "TODO/FIXMEコメントが含まれています",
                "suggestion": "Issue化するか、実装を完了してください"
            })

    return issues


def analyze_security(files: List[Dict]) -> List[Dict]:
    """
    セキュリティを分析

    Args:
        files: 変更されたファイルのリスト

    Returns:
        セキュリティ問題のリスト
    """
    issues = []

    for file_info in files:
        filename = file_info["filename"]
        patch = file_info.get("patch", "")

        # ハードコードされたシークレットのチェック
        for pattern in SECURITY_PATTERNS["hardcoded_secrets"]:
            if re.search(pattern, patch, re.IGNORECASE):
                issues.append({
                    "severity": "critical",
                    "category": "security",
                    "file": filename,
                    "message": "ハードコードされたシークレット（パスワード、API key等）の可能性があります",
                    "suggestion": "環境変数やシークレット管理システムを使用してください"
                })
                break

        # SQLインジェクションのチェック
        for pattern in SECURITY_PATTERNS["sql_injection"]:
            if re.search(pattern, patch):
                issues.append({
                    "severity": "critical",
                    "category": "security",
                    "file": filename,
                    "message": "SQLインジェクションの脆弱性の可能性があります",
                    "suggestion": "プリペアドステートメントやORM を使用してください"
                })
                break

        # XSS脆弱性のチェック
        for pattern in SECURITY_PATTERNS["xss_vulnerability"]:
            if re.search(pattern, patch):
                issues.append({
                    "severity": "major",
                    "category": "security",
                    "file": filename,
                    "message": "XSS脆弱性の可能性があります",
                    "suggestion": "ユーザー入力は適切にサニタイズしてください"
                })
                break

    return issues


def analyze_testing(files: List[Dict], pr_info: Dict) -> List[Dict]:
    """
    テストを分析

    Args:
        files: 変更されたファイルのリスト
        pr_info: PR情報

    Returns:
        テスト関連の問題のリスト
    """
    issues = []

    # テストファイルの存在チェック
    test_files = [
        f for f in files
        if "test" in f["filename"].lower() or "spec" in f["filename"].lower()
    ]

    source_files = [
        f for f in files
        if f["filename"].endswith((".py", ".js", ".ts", ".java", ".go"))
        and "test" not in f["filename"].lower()
        and "spec" not in f["filename"].lower()
    ]

    if source_files and not test_files:
        issues.append({
            "severity": "major",
            "category": "testing",
            "file": None,
            "message": "ソースコードが変更されていますが、テストが追加されていません",
            "suggestion": "新しい機能や変更に対するテストを追加してください"
        })

    # テストファイルのサイズチェック
    for test_file in test_files:
        if test_file["additions"] < 10:
            issues.append({
                "severity": "minor",
                "category": "testing",
                "file": test_file["filename"],
                "message": "テストの追加が少ないようです",
                "suggestion": "エッジケースを含む十分なテストケースを追加してください"
            })

    return issues


def analyze_performance(files: List[Dict]) -> List[Dict]:
    """
    パフォーマンスを分析

    Args:
        files: 変更されたファイルのリスト

    Returns:
        パフォーマンス関連の問題のリスト
    """
    issues = []

    for file_info in files:
        filename = file_info["filename"]
        patch = file_info.get("patch", "")

        # N+1クエリ問題のチェック
        for pattern in PERFORMANCE_PATTERNS["n_plus_one"]:
            if re.search(pattern, patch):
                issues.append({
                    "severity": "major",
                    "category": "performance",
                    "file": filename,
                    "message": "N+1クエリ問題の可能性があります",
                    "suggestion": "一括クエリや事前読み込み（eager loading）の使用を検討してください"
                })
                break

        # 非効率なループのチェック
        for pattern in PERFORMANCE_PATTERNS["inefficient_loop"]:
            if re.search(pattern, patch):
                issues.append({
                    "severity": "minor",
                    "category": "performance",
                    "file": filename,
                    "message": "3重以上のネストされたループがあります",
                    "suggestion": "アルゴリズムの最適化を検討してください"
                })
                break

    return issues


def categorize_findings(findings: List[Dict]) -> Dict:
    """
    検出結果をカテゴリーと重要度別に集計

    Args:
        findings: 検出結果のリスト

    Returns:
        カテゴリー別の集計結果
    """
    categorized = {
        "critical": [],
        "major": [],
        "minor": [],
        "suggestion": []
    }

    for finding in findings:
        severity = finding.get("severity", "suggestion")
        categorized[severity].append(finding)

    return categorized


def calculate_scores(categorized_findings: Dict) -> Dict:
    """
    各カテゴリーのスコアを計算（10点満点）

    Args:
        categorized_findings: カテゴリー別の検出結果

    Returns:
        カテゴリー別スコア
    """
    scores = {
        "code_quality": 10,
        "security": 10,
        "testing": 10,
        "performance": 10
    }

    # 重要度に応じて減点
    severity_weights = {
        "critical": 3,
        "major": 2,
        "minor": 1,
        "suggestion": 0.5
    }

    for severity, findings in categorized_findings.items():
        weight = severity_weights.get(severity, 0)
        for finding in findings:
            category = finding.get("category", "code_quality")
            if category in scores:
                scores[category] = max(0, scores[category] - weight)

    return scores


def analyze_pr(pr_data: Dict) -> Dict:
    """
    PRを包括的に分析

    Args:
        pr_data: PR情報

    Returns:
        分析結果
    """
    files = pr_data.get("files", [])

    print("Analyzing code quality...", file=sys.stderr)
    quality_issues = analyze_code_quality(files)

    print("Analyzing security...", file=sys.stderr)
    security_issues = analyze_security(files)

    print("Analyzing testing...", file=sys.stderr)
    testing_issues = analyze_testing(files, pr_data)

    print("Analyzing performance...", file=sys.stderr)
    performance_issues = analyze_performance(files)

    # 全ての問題を統合
    all_findings = quality_issues + security_issues + testing_issues + performance_issues

    # カテゴリー別に分類
    categorized = categorize_findings(all_findings)

    # スコア計算
    scores = calculate_scores(categorized)

    result = {
        "pr_url": pr_data.get("pr_url"),
        "pr_number": pr_data.get("pr_number"),
        "title": pr_data.get("title"),
        "author": pr_data.get("author"),
        "scores": scores,
        "findings": {
            "critical": categorized["critical"],
            "major": categorized["major"],
            "minor": categorized["minor"],
            "suggestion": categorized["suggestion"]
        },
        "summary": {
            "total_issues": len(all_findings),
            "critical_count": len(categorized["critical"]),
            "major_count": len(categorized["major"]),
            "minor_count": len(categorized["minor"]),
            "suggestion_count": len(categorized["suggestion"])
        },
        "recommendation": determine_recommendation(categorized)
    }

    return result


def determine_recommendation(categorized_findings: Dict) -> str:
    """
    分析結果から推奨アクションを決定

    Args:
        categorized_findings: カテゴリー別の検出結果

    Returns:
        推奨アクション（APPROVE, CONDITIONAL_APPROVE, REQUEST_CHANGES）
    """
    if categorized_findings["critical"]:
        return "REQUEST_CHANGES"
    elif categorized_findings["major"] or categorized_findings["minor"]:
        return "CONDITIONAL_APPROVE"
    else:
        return "APPROVE"


def main():
    parser = argparse.ArgumentParser(
        description="Analyze GitHub PR for code quality, security, testing, and performance"
    )
    parser.add_argument(
        "--pr-data",
        required=True,
        help="Path to PR data JSON file (output from fetch_pr_info.py)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path (default: stdout)"
    )

    args = parser.parse_args()

    try:
        # PR情報を読み込み
        with open(args.pr_data, "r", encoding="utf-8") as f:
            pr_data = json.load(f)

        # 分析実行
        result = analyze_pr(pr_data)

        # 出力
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Analysis result saved to {args.output}", file=sys.stderr)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
