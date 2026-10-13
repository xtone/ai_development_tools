import copy
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import load_cards  # noqa: E402
import synth  # noqa: E402

CATALOG = load_cards.load_questions(load_cards.DEFAULT_QUESTIONS)
TOPICS = load_cards.load_topics([Path(load_cards.CARDS_SCRIPTS).parents[2] / "confidential_topics.json"], require=True)


def row(n, question, polarity, claim, project="app-a", author="user://u1", confidence="observed", context="文脈。", evidence="根拠"):
    return {
        "url": f"https://app.notion.com/p/card{n}",
        "カード": claim,
        "問い": question,
        "プロジェクト": json.dumps([project]),
        "極性": polarity,
        "確度": confidence,
        "タグ": json.dumps(["prompt"]),
        "文脈": context,
        "根拠": evidence,
        "投稿者": json.dumps([author]),
        "公開範囲": "internal",
    }


ROWS = [
    row(1, "P1", "fact", "app-a: 管理画面を実装中"),
    row(2, "Q1", "worked", "目的を 1 文で伝えると承認だけで PR まで進んだ"),
    row(3, "Q2", "failed", "誰の代わりに動くかを書かずに調査を頼み、前提を言い直した", project="app-b", author="user://u2"),
    row(4, "Q7", "failed", "正規表現の性能テストを先に入れれば ReDoS を防げた", confidence="inferred"),
    row(5, "Q2", "failed", "誰の代わりに動くかを書かずに調査を頼み、前提を言い直した。", project="app-b", author="user://u2"),
    row(6, "Q1", "worked", "取締役会の資料を一発で作れた依頼の書き方がある"),
    row(7, "Q1", "worked", "ADR の昇格を頼むと一発で通った", project="app-c", author="user://u3"),
]


def loaded(rows=ROWS):
    return {"week": "2026-W43", "title": "2026-W43（10/19〜10/25）", **load_cards.load(rows, CATALOG, TOPICS)}


def u(n):
    return f"https://app.notion.com/p/card{n}"


def themes(**over):
    base = {
        "week": "2026-W43",
        "themes": [
            {
                "title": "前提を書かずに頼めるのは、問い返す手順を挟むときだけ",
                "cards": [u(2), u(3)],
                "conflict": "正「目的を 1 文で伝えて通った」と反「前提を書かずに言い直した」。分かれ目は問い返しの有無（推定）",
                "kinds": ["条件分け", "仕組み化"],
                "proposal": "調査の依頼では、誰が何のために使うかを最初に書く。テンプレを CLAUDE.md に置く",
                "limits": "参加者が少ない",
            },
            {
                "title": "入力に依存する処理は、計画の段階でテストを決める",
                "cards": [u(4)],
                "conflict": "",
                "kinds": ["仕組み化"],
                "proposal": "実装計画に性能テストを入れる",
                "limits": "手戻りの量はカードから言えない",
            },
            {
                "title": "業務用語の昇格は依頼文に書けば通る",
                "cards": [u(7)],
                "conflict": "",
                "kinds": ["両立案"],
                "proposal": "ADR の昇格条件を依頼文に書く",
                "limits": "1 枚のみ",
            },
        ],
        "next_questions": [{"id": "Q4", "reason": "手戻りの大きさを知るため"}],
    }
    base.update(over)
    return base


# ---- load_cards ----


def test_load_splits_facts_and_opinions_and_anonymizes_authors():
    data = loaded()
    assert [c["url"] for c in data["facts"]] == [u(1)]
    assert {c["url"] for c in data["opinions"]} == {u(2), u(3), u(4), u(7)}
    assert {c["person"] for c in data["opinions"]} == {"p1", "p2", "p3"}
    assert "user://" not in json.dumps(data)
    assert data["metrics"]["by_question"] == {"P1": 1, "Q1": 2, "Q2": 1, "Q7": 1}
    assert data["metrics"]["people"] == 3 and data["metrics"]["observed"] == 4


def test_load_merges_duplicates_and_drops_confidential_cards():
    data = loaded()
    card3 = next(c for c in data["opinions"] if c["url"] == u(3))
    assert card3["duplicates"] == [u(5)]
    assert data["excluded"] == {"duplicates": 1, "confidential": 1}
    assert u(6) not in json.dumps(data)  # strong word (取締役)
    card7 = next(c for c in data["opinions"] if c["url"] == u(7))
    assert card7["review_words"] == ["昇格"]  # review word kept, its author cleared it


def test_same_claim_by_another_person_is_not_a_duplicate():
    rows = [row(1, "Q1", "worked", "目的を 1 文で伝えると承認だけで PR まで進んだ"),
            row(2, "Q1", "worked", "目的を 1 文で伝えると承認だけで PR まで進んだ", author="user://u9")]
    assert len(loaded(rows)["opinions"]) == 2


def test_load_cli_reads_mcp_query_output(tmp_path):
    q = tmp_path / "q1.json"
    q.write_text(json.dumps({"results": ROWS[:3], "has_more": False}, ensure_ascii=False), encoding="utf-8")
    q2 = tmp_path / "q2.json"
    q2.write_text(json.dumps(ROWS[2:4], ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "cards.json"
    r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "load_cards.py"), q, q2, "--week", "2026-W43", "--out", out],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["title"] == "2026-W43（10/19〜10/25）" and data["metrics"]["cards"] == 4


# ---- validate ----


def errors_of(t):
    return synth.validate(t, loaded(), CATALOG)[0]


def test_valid_themes_pass():
    assert synth.validate(themes(), loaded(), CATALOG) == ([], [])


def test_validate_requires_conflict_when_worked_and_failed_meet():
    t = themes()
    t["themes"][0]["conflict"] = ""
    assert any("write the conflict" in e for e in errors_of(t))


def test_validate_rejects_bad_themes():
    t = themes()
    t["themes"][1]["title"] = "テストについて"
    t["themes"][1]["kinds"] = ["改善"]
    t["themes"][1]["limits"] = ""
    t["themes"][2]["cards"] = [u(1)]
    errs = errors_of(t)
    assert any("について" in e or "chars" in e for e in errs)
    assert any("kinds must be" in e for e in errs)
    assert any("limits is empty" in e for e in errs)
    assert any("fact card" in e for e in errs)
    assert any(u(7) in e and "no theme" in e for e in errs)


def test_validate_rejects_person_labels_and_unknown_questions():
    t = themes(next_questions=[{"id": "Q99", "reason": "x"}, {"reason": ""}])
    t["themes"][1]["proposal"] = "p2 の書き方を全員に広める"
    errs = errors_of(t)
    assert any("author label" in e for e in errs)
    assert any("unknown id Q99" in e for e in errs)
    assert any("needs an id" in e for e in errs)


def test_strength_and_question_come_from_cards():
    rich = synth.enrich(themes()["themes"][0], synth.card_index(loaded()), CATALOG)
    assert rich["question"] == "Q1"  # Q1 and Q2 tie; catalog order wins
    assert (rich["people"], rich["projects"], rich["count"]) == (2, 2, 2)


# ---- render / check / to-notion ----


def test_render_follows_the_template_and_codes_filenames():
    md = synth.render(themes(), loaded(), CATALOG)
    assert md.startswith('<callout icon="🧭" color="gray_bg">')
    assert "\t2026-W43（10/19〜10/25）のナレッジカードの合成。参加者 3 人・カード 5 枚から、テーマ 3・対立 1・提案 3" in md
    for heading in ("## 指標", "## 共有会で決めること", "## テーマと合", "## 今週動いていたプロジェクト", "## 次の問い"):
        assert heading in md
    assert f'<mention-page url="{u(2)}"/>（Q1・worked・app-a）' in md
    assert "- **共通解**（対立なし）" in md
    assert "`CLAUDE.md`" in md and "``CLAUDE.md``" not in md
    assert "<td>管理画面を実装中</td>" in md
    assert "- Q4（手戻りが最も大きかった作業" in md
    assert "2 人・2 プロジェクト・2 枚（observed 2）" in md
    assert "p1" not in md and "p2" not in md


def test_render_mentions_theme_pages_when_urls_are_known():
    t = themes()
    md = synth.render(t, loaded(), CATALOG, {t["themes"][0]["title"]: "https://app.notion.com/p/theme1"})
    assert '（テーマ: <mention-page url="https://app.notion.com/p/theme1"/>）' in md


def test_check_ignores_mentions_and_allows_cleared_review_words():
    data = loaded()
    md = synth.render(themes(), data, CATALOG)
    assert synth.check(md, data, TOPICS) == []  # notion URLs in mentions, 昇格 cleared by the card's author


def test_check_flags_new_confidential_text_and_secrets():
    data = loaded()
    md = synth.render(themes(), data, CATALOG) + "\n- 経営会議で共有する\n- 退職の件\n- token HnRXa1s7-80Y6Hrv8HhTcG_sqvqRy0nGUlqhG9pqeL8\n"
    problems = synth.check(md, data, TOPICS)
    assert any("strong" in p and "経営" in p for p in problems)
    assert any("review" in p and "退職" in p for p in problems)
    assert any("token" in p for p in problems)


def test_to_notion_properties():
    pages = synth.to_notion(themes(), loaded(), CATALOG, "https://app.notion.com/week")
    p = pages[0]["properties"]
    assert p["週"] == ["https://app.notion.com/week"] and p["問い"] == "Q1" and p["採否"] == "検討中"
    assert p["カード"] == [u(2), u(3)]
    assert p["合"].startswith("条件分け＋仕組み化: ") and "根拠: 2 人・2 プロジェクト・2 枚" in p["合"]
    assert pages[1]["properties"]["対立"] == ""


def test_cli_validate_render_check(tmp_path):
    cards = tmp_path / "cards.json"
    cards.write_text(json.dumps(loaded(), ensure_ascii=False), encoding="utf-8")
    th = tmp_path / "themes.json"
    th.write_text(json.dumps(themes(), ensure_ascii=False), encoding="utf-8")
    run = lambda *a: subprocess.run([sys.executable, "-I", str(SCRIPTS / "synth.py"), *map(str, a)], capture_output=True, text=True)
    assert run("validate", th, "--cards", cards).returncode == 0
    md = tmp_path / "summary.md"
    assert run("render", th, "--cards", cards, "--out", md).returncode == 0
    r = run("check", md, "--cards", cards)
    assert r.returncode == 0, r.stdout
    bad = copy.deepcopy(themes())
    bad["themes"][0]["conflict"] = ""
    th.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    assert run("validate", th, "--cards", cards).returncode == 1
