#!/usr/bin/env python3
"""TPL-27 補助 — JSON Schema 検証（YAML 対応）。

Usage:
    validate_schema.py <schema.json> <data-file.json|.yaml> [--label LABEL]

成果:
    検証 OK   -> stdout に `✅ <label>: OK`、終了コード 0
    検証 NG   -> stderr に `⚠️  <label>: <エラー>`、終了コード 1
    依存欠如  -> stderr に手当案内、終了コード 2（warn_and_document で呼び出し側が握り潰す）

依存:
    jsonschema, PyYAML（YAML 検証時のみ）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


class DependencyMissing(Exception):
    """jsonschema / PyYAML 等の依存ライブラリが未導入。warn_and_document で exit 2 に対応。"""


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise DependencyMissing(
            "PyYAML 未導入のため YAML 検証をスキップ: "
            "pip3 install --user PyYAML jsonschema"
        ) from e
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_data(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _load_yaml(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="JSON Schema 検証（YAML 可）")
    parser.add_argument("schema", type=Path, help="JSON Schema ファイル")
    parser.add_argument("data", type=Path, help="検証対象ファイル（.json / .yaml）")
    parser.add_argument("--label", default=None, help="出力ラベル（既定: data のパス）")
    args = parser.parse_args()

    label = args.label or str(args.data)

    try:
        import jsonschema  # type: ignore
    except ImportError:
        print(
            "⚠️  jsonschema 未導入のためスキーマ検証をスキップ: "
            "pip3 install --user jsonschema PyYAML",
            file=sys.stderr,
        )
        return 2

    try:
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️  {label}: スキーマ読み込み失敗 ({args.schema}): {e}", file=sys.stderr)
        return 1

    try:
        data = _load_data(args.data)
    except DependencyMissing as e:
        print(f"⚠️  {e}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as e:
        print(f"⚠️  {label}: データ読み込み失敗: {e}", file=sys.stderr)
        return 1

    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)

    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if not errors:
        print(f"✅ {label}: OK")
        return 0

    for err in errors:
        path = "$" + "".join(f"[{p!r}]" for p in err.absolute_path)
        print(f"⚠️  {label}: {path} — {err.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
