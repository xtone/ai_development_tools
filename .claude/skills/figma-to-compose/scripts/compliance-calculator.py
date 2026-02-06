#!/usr/bin/env python3
"""
Figma Compliance Calculator

Figma仕様と生成されたComposeコードの準拠率を計算するスクリプト。

Usage:
    python compliance-calculator.py --figma-spec figma-spec.json --compose-impl Component.kt

Output:
    - 準拠率スコアカード（Markdown形式）
    - Before/After比較レポート
"""

import argparse
import json
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ComplianceLevel(Enum):
    """準拠レベル"""
    EXCELLENT = "EXCELLENT"  # 95%以上
    GOOD = "GOOD"            # 80%以上95%未満
    POOR = "POOR"            # 80%未満


@dataclass
class ComplianceItem:
    """準拠チェック項目"""
    category: str
    item_name: str
    figma_value: str
    compose_value: str
    is_match: bool
    score: int
    max_score: int


@dataclass
class ComplianceReport:
    """準拠率レポート"""
    component_name: str
    node_id: str
    items: List[ComplianceItem]
    total_score: int
    max_total_score: int
    compliance_rate: float
    level: ComplianceLevel


class FigmaSpecParser:
    """Figma仕様パーサー"""

    @staticmethod
    def parse(figma_spec_path: str) -> Dict:
        """Figma仕様JSONを解析"""
        with open(figma_spec_path, 'r', encoding='utf-8') as f:
            return json.load(f)


class ComposeCodeParser:
    """Composeコードパーサー"""

    @staticmethod
    def parse(compose_file_path: str) -> Dict:
        """Composeコードから値を抽出"""
        with open(compose_file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        return {
            'colors': ComposeCodeParser._extract_colors(code),
            'typography': ComposeCodeParser._extract_typography(code),
            'layout': ComposeCodeParser._extract_layout(code),
        }

    @staticmethod
    def _extract_colors(code: str) -> Dict[str, str]:
        """Color定義を抽出"""
        colors = {}
        # Color(0xFFRRGGBB) パターンを抽出
        pattern = r'val\s+(\w+)\s*=\s*Color\((0x[0-9A-Fa-f]{8})\)'
        for match in re.finditer(pattern, code):
            colors[match.group(1)] = match.group(2)
        return colors

    @staticmethod
    def _extract_typography(code: str) -> Dict[str, Dict]:
        """Typography定義を抽出"""
        typography = {}
        # TextStyle定義を探す（簡易版）
        pattern = r'val\s+(\w+)\s*=\s*TextStyle\((.*?)\)'
        for match in re.finditer(pattern, code, re.DOTALL):
            name = match.group(1)
            content = match.group(2)

            # fontSize抽出
            font_size_match = re.search(r'fontSize\s*=\s*(\d+(?:\.\d+)?)\s*\.sp', content)
            # fontWeight抽出
            font_weight_match = re.search(r'fontWeight\s*=\s*FontWeight\.(\w+)', content)
            # lineHeight抽出
            line_height_match = re.search(r'lineHeight\s*=\s*(\d+(?:\.\d+)?)\s*\.sp', content)

            typography[name] = {
                'fontSize': font_size_match.group(1) if font_size_match else None,
                'fontWeight': font_weight_match.group(1) if font_weight_match else None,
                'lineHeight': line_height_match.group(1) if line_height_match else None,
            }
        return typography

    @staticmethod
    def _extract_layout(code: str) -> Dict[str, str]:
        """Layout定義を抽出"""
        layout = {}
        # LayoutDimensionsオブジェクト内の定数を抽出
        pattern = r'val\s+(\w+)\s*=\s*(\d+(?:\.\d+)?)\s*\.dp'
        for match in re.finditer(pattern, code):
            layout[match.group(1)] = match.group(2)

        # RoundedCornerShape抽出
        corner_match = re.search(r'RoundedCornerShape\((\d+(?:\.\d+)?)\s*\.dp\)', code)
        if corner_match:
            layout['cornerRadius'] = corner_match.group(1)

        return layout


class ComplianceCalculator:
    """準拠率計算"""

    def __init__(self, figma_spec: Dict, compose_impl: Dict):
        self.figma_spec = figma_spec
        self.compose_impl = compose_impl
        self.items: List[ComplianceItem] = []

    def calculate(self) -> ComplianceReport:
        """準拠率を計算"""
        # Color準拠チェック
        self._check_colors()

        # Typography準拠チェック
        self._check_typography()

        # Layout準拠チェック
        self._check_layout()

        # スコア集計
        total_score = sum(item.score for item in self.items)
        max_total_score = sum(item.max_score for item in self.items)
        compliance_rate = (total_score / max_total_score * 100) if max_total_score > 0 else 0

        # レベル判定
        if compliance_rate >= 95:
            level = ComplianceLevel.EXCELLENT
        elif compliance_rate >= 80:
            level = ComplianceLevel.GOOD
        else:
            level = ComplianceLevel.POOR

        return ComplianceReport(
            component_name=self.figma_spec.get('component_name', 'Unknown'),
            node_id=self.figma_spec.get('node_id', 'Unknown'),
            items=self.items,
            total_score=total_score,
            max_total_score=max_total_score,
            compliance_rate=compliance_rate,
            level=level
        )

    def _check_colors(self):
        """Color準拠をチェック"""
        figma_colors = self.figma_spec.get('colors', {})
        compose_colors = self.compose_impl.get('colors', {})

        for color_name, figma_value in figma_colors.items():
            compose_value = compose_colors.get(color_name, 'NOT_FOUND')
            is_match = figma_value.upper() == compose_value.upper()

            self.items.append(ComplianceItem(
                category='Color',
                item_name=color_name,
                figma_value=figma_value,
                compose_value=compose_value,
                is_match=is_match,
                score=5 if is_match else 0,
                max_score=5
            ))

    def _check_typography(self):
        """Typography準拠をチェック"""
        figma_typography = self.figma_spec.get('typography', {})
        compose_typography = self.compose_impl.get('typography', {})

        for typo_name, figma_values in figma_typography.items():
            compose_values = compose_typography.get(typo_name, {})

            # fontSize
            figma_font_size = str(figma_values.get('fontSize', ''))
            compose_font_size = compose_values.get('fontSize', 'NOT_FOUND')
            font_size_match = figma_font_size == compose_font_size

            self.items.append(ComplianceItem(
                category='Typography',
                item_name=f'{typo_name}.fontSize',
                figma_value=f'{figma_font_size}px',
                compose_value=f'{compose_font_size}.sp' if compose_font_size != 'NOT_FOUND' else 'NOT_FOUND',
                is_match=font_size_match,
                score=8 if font_size_match else 0,
                max_score=8
            ))

            # fontWeight
            figma_font_weight = figma_values.get('fontWeight', '')
            compose_font_weight = compose_values.get('fontWeight', 'NOT_FOUND')
            # fontWeightマッピング（700 → Bold等）
            weight_map = {
                '700': 'Bold',
                '600': 'SemiBold',
                '500': 'Medium',
                '400': 'Normal',
                '300': 'Light',
            }
            expected_weight = weight_map.get(str(figma_font_weight), str(figma_font_weight))
            font_weight_match = expected_weight == compose_font_weight

            self.items.append(ComplianceItem(
                category='Typography',
                item_name=f'{typo_name}.fontWeight',
                figma_value=str(figma_font_weight),
                compose_value=f'FontWeight.{compose_font_weight}' if compose_font_weight != 'NOT_FOUND' else 'NOT_FOUND',
                is_match=font_weight_match,
                score=8 if font_weight_match else 0,
                max_score=8
            ))

    def _check_layout(self):
        """Layout準拠をチェック"""
        figma_layout = self.figma_spec.get('layout', {})
        compose_layout = self.compose_impl.get('layout', {})

        for layout_name, figma_value in figma_layout.items():
            compose_value = compose_layout.get(layout_name, 'NOT_FOUND')
            is_match = str(figma_value) == str(compose_value)

            self.items.append(ComplianceItem(
                category='Layout',
                item_name=layout_name,
                figma_value=f'{figma_value}px',
                compose_value=f'{compose_value}.dp' if compose_value != 'NOT_FOUND' else 'NOT_FOUND',
                is_match=is_match,
                score=6 if is_match else 0,
                max_score=6
            ))


class ReportGenerator:
    """レポート生成"""

    @staticmethod
    def generate_markdown(report: ComplianceReport) -> str:
        """Markdownレポートを生成"""
        md = []

        # ヘッダー
        md.append("# Implementation Compliance Report\n")
        md.append(f"## Component: {report.component_name}")
        md.append(f"## Node ID: {report.node_id}\n")

        # カテゴリ別スコア
        categories = {}
        for item in report.items:
            if item.category not in categories:
                categories[item.category] = {'score': 0, 'max_score': 0, 'items': []}
            categories[item.category]['score'] += item.score
            categories[item.category]['max_score'] += item.max_score
            categories[item.category]['items'].append(item)

        # カテゴリ別詳細
        for category, data in categories.items():
            cat_rate = (data['score'] / data['max_score'] * 100) if data['max_score'] > 0 else 0
            status = "✅" if cat_rate == 100 else "⚠️"
            md.append(f"\n### {category} Compliance: {data['score']} / {data['max_score']}点 ({cat_rate:.1f}%) {status}\n")

            md.append("| 項目 | Figma仕様 | Compose実装 | 一致 | 配点 | 獲得点 |")
            md.append("|------|----------|------------|------|------|--------|")

            for item in data['items']:
                status_icon = "✅" if item.is_match else "❌"
                md.append(f"| {item.item_name} | {item.figma_value} | {item.compose_value} | {status_icon} | {item.max_score} | {item.score} |")

        # 総合スコア
        md.append(f"\n## Overall Compliance Score\n")
        md.append(f"### Total: {report.total_score} / {report.max_total_score}点 ({report.compliance_rate:.1f}%)\n")

        # 判定
        if report.level == ComplianceLevel.EXCELLENT:
            md.append("### 判定: ✅ **EXCELLENT** (95%以上)")
        elif report.level == ComplianceLevel.GOOD:
            md.append("### 判定: ⚠️ **GOOD** (80%以上95%未満) - 要改善")
        else:
            md.append("### 判定: ❌ **POOR** (80%未満) - 再実装推奨")

        # 不一致項目
        mismatches = [item for item in report.items if not item.is_match]
        if mismatches:
            md.append("\n## Improvement Required\n")
            md.append("### 不一致項目\n")
            for item in mismatches:
                md.append(f"- [ ] **{item.item_name}**: {item.compose_value} → {item.figma_value} に修正")

        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description='Figma Compliance Calculator')
    parser.add_argument('--figma-spec', required=True, help='Figma仕様JSONファイルパス')
    parser.add_argument('--compose-impl', required=True, help='Compose実装ファイルパス')
    parser.add_argument('--output', default='compliance-report.md', help='出力レポートファイルパス')

    args = parser.parse_args()

    # Figma仕様を解析
    figma_spec = FigmaSpecParser.parse(args.figma_spec)

    # Composeコードを解析
    compose_impl = ComposeCodeParser.parse(args.compose_impl)

    # 準拠率を計算
    calculator = ComplianceCalculator(figma_spec, compose_impl)
    report = calculator.calculate()

    # レポートを生成
    markdown_report = ReportGenerator.generate_markdown(report)

    # ファイル出力
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(markdown_report)

    print(f"✅ Compliance report generated: {args.output}")
    print(f"📊 Overall Score: {report.compliance_rate:.1f}% ({report.level.value})")


if __name__ == '__main__':
    main()
