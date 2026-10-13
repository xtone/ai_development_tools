import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("topics", SCRIPTS / "topics.py")
topics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topics)

DEFAULT = topics.load_topics([topics.DEFAULT_FILE])


@pytest.mark.parametrize(
    "text, expected",
    [
        ("来期の人事評価のコメントを下書きして", "evaluation"),
        ("メンバーの評価を整理したい", "evaluation"),
        ("賞与の配分案を表にして", "evaluation"),
        ("ボーナスの配分を決めたい", "evaluation"),
        ("昇格要件を整理して", "evaluation"),
        ("1on1 のメモをまとめて", "evaluation"),
        ("自己評価シートを書いて", "evaluation"),
        ("メンバーの退職について相談", "management"),
        ("退職勧奨の進め方", "management"),
        ("取締役会の資料を作って", "management"),
        ("Xtone の中期経営計画をレビューして", "management"),
        ("PKSHA との資本業務提携の論点", "management"),
        ("IR 資料の数字を確認", "management"),
        ("来期の予算策定のたたき台", "management"),
        ("ＰＫＳＨＡの決算説明会", "management"),
    ],
)
def test_confidential_topics_match(text, expected):
    assert topics.match_topic(text, DEFAULT) == expected


@pytest.mark.parametrize(
    "text",
    [
        "https://app.notion.com/p/pkshagroup/<redacted> 管理画面の設計",
        "https://github.com/xtone/akita-shoten/pull/227 をマージしました",
        "LLM のトークン予算とレート制限",
        "モデルの評価指標を足して",
        "動画生成にも「評価と改善」の項目を追加",
        "cd ~/.claude/dir && irb を起動",
        "4rcit6K4IrhiuKK5+Ir6iv6LAIsBiwKLB",
        "Mermaid の図を修正してください",
    ],
)
def test_ordinary_development_text_does_not_match(text):
    assert topics.classify(text, DEFAULT) is None


@pytest.mark.parametrize(
    "text, word",
    [
        ("管理者向けに退職者処理の機能を追加したい", "退職"),
        ("退職の件で相談したい", "退職"),
        ("`!` 演算子の評価結果は 0 か 1", "評価結果"),
        ("その自己評価も不正確だった", "自己評価"),
        ("ADR を昇格させてください", "昇格"),
        ("SKILL.md 昇格候補は次回判断", "昇格"),
        ("verify 省略ボーナス事例を記録", "ボーナス"),
        ("IR の数字を確認", "IR"),
    ],
)
def test_ambiguous_words_are_held_for_review(text, word):
    hit = topics.classify(text, DEFAULT)
    assert hit is not None and hit[1] == "review" and hit[2] == word
    assert topics.match_topic(text, DEFAULT) is not None  # excluded by default (fail closed)
    assert topics.blocked(text, DEFAULT, allow_review=True) is None


def test_allowing_a_review_word_never_hides_a_strong_word():
    text = "退職者処理の画面と取締役会の資料"
    assert topics.blocked(text, DEFAULT, allowed_terms=["退職"])[1] == "strong"
    assert topics.blocked(text, DEFAULT, allow_review=True)[1] == "strong"
    assert topics.blocked("退職者処理の画面", DEFAULT, allowed_terms=["退職"]) is None


def test_local_file_adds_patterns_to_the_same_topic(tmp_path):
    extra = tmp_path / "extra.json"
    extra.write_text(json.dumps({"topics": [{"id": "management", "patterns": ["極秘プロジェクトX"]}]}), encoding="utf-8")
    loaded = topics.load_topics([topics.DEFAULT_FILE, extra])
    assert topics.match_topic("極秘プロジェクトX の件", loaded) == "management"
    assert topics.match_topic("取締役会", loaded) == "management"
    assert len(loaded) == 2


def test_bad_pattern_is_an_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"topics": [{"id": "x", "patterns": ["("]}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        topics.load_topics([bad])
