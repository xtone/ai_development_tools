import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
CARDS = SCRIPTS / "cards.py"
QUESTIONS = SCRIPTS.parents[2] / "questions.json"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cards = _load("cards")
CATALOG = cards.load_questions(QUESTIONS)


def card(**over):
    base = {
        "card_id": "2026-W43/Q2/y.toyota/001",
        "question_id": "Q2",
        "week": "2026-W43",
        "week_range": ["2026-10-19", "2026-10-25"],
        "author_email": "y.toyota@example.com",
        "project": "ai_development_tools",
        "claim": "完了条件を書かずに依頼し、テストの範囲で 2 回言い直した",
        "context": "週の計算を直す依頼で、どのテストを通せば終わりかを書かなかった。",
        "polarity": "failed",
        "confidence": "observed",
        "evidence": [
            {"type": "prompt", "ref": "abc-1@2026-10-20T10:12", "excerpt": "週の計算を直して"},
            {"type": "prompt", "ref": "abc-1@2026-10-20T10:20", "excerpt": "年またぎも\nテストして"},
        ],
        "tags": ["prompt", "testing"],
        "sensitivity": "internal",
        "status": "draft",
        "notion_url": None,
    }
    base.update(over)
    return base


def run(*args):
    return subprocess.run([sys.executable, "-I", str(CARDS), *map(str, args)], capture_output=True, text=True)


# ---- weeks ----


def test_week_info_title_and_range():
    info = cards.week_info("2026-W43")
    assert info == {
        "week": "2026-W43",
        "monday": "2026-10-19",
        "sunday": "2026-10-25",
        "title": "2026-W43（10/19〜10/25）",
    }


def test_previous_week_and_year_boundary():
    assert cards.previous_week(cards.dt.date(2026, 10, 13)) == "2026-W41"
    assert cards.next_week("2026-W53") == "2027-W01"
    assert cards.week_info("2027-W01")["monday"] == "2027-01-04"
    assert cards.week_info("2026-W53")["sunday"] == "2027-01-03"
    assert cards.previous_week(cards.dt.date(2027, 1, 6)) == "2026-W53"


def test_week_rejects_bad_ids():
    for bad in ("2026-43", "2025-W53", "2026-W00"):
        with pytest.raises(cards.InputError):
            cards.week_info(bad)


def test_week_cli_defaults_to_previous_week():
    r = run("week", "--today", "2026-10-26")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["week"] == "2026-W43"


# ---- plan ----


def test_plan_adds_rotation_from_epoch():
    assert [q["id"] for q in cards.plan(CATALOG, "2026-W43")] == ["P1", "Q1", "Q2", "Q3"]
    assert [q["id"] for q in cards.plan(CATALOG, "2026-W44")][-1] == "Q4"
    assert [q["id"] for q in cards.plan(CATALOG, "2026-W48")][-1] == "Q3"
    assert [q["id"] for q in cards.plan(CATALOG, "2026-W42")][-1] == "Q9"


def test_plan_ids_override_and_reject_unknown():
    assert [q["id"] for q in cards.plan(CATALOG, "2026-W43", ["Q5", "P2"])] == ["Q5", "P2"]
    with pytest.raises(cards.InputError):
        cards.plan(CATALOG, "2026-W43", ["Q99"])


def test_catalog_matches_notion_options():
    ids = [q["id"] for q in CATALOG["questions"]]
    assert ids == ["P1", "P2", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9"]
    for q in CATALOG["questions"]:
        assert q["polarity"] in cards.POLARITIES
        assert q["text"] and q["draft_hint"]


# ---- validate ----


def errors_of(*cs):
    return cards.validate(list(cs), CATALOG)[0]


def test_valid_card_passes():
    assert cards.validate([card()], CATALOG) == ([], [])


@pytest.mark.parametrize(
    "over, fragment",
    [
        ({"claim": "短すぎる"}, "min 20"),
        ({"claim": "あ" * 81}, "max 80"),
        ({"claim": "Claude Code に依頼するときのテスト範囲の書き方について"}, "について"),
        ({"evidence": []}, "at least one"),
        ({"evidence": [{"type": "chat", "ref": "x", "excerpt": "y"}]}, "type must be"),
        ({"evidence": [{"type": "prompt", "ref": "", "excerpt": "y"}]}, "ref is empty"),
        ({"evidence": [{"type": "session", "ref": "abc@10:00", "excerpt": "y"}]}, "<session_id>#<uuid>"),
        ({"evidence": [{"type": "prompt", "ref": "x", "excerpt": "あ" * 121}]}, "max 120"),
        ({"evidence": [{"type": "prompt", "ref": f"x{i}", "excerpt": "y"} for i in range(4)]}, "max 3"),
        ({"polarity": "worked"}, "not allowed for Q2"),
        ({"polarity": "great"}, "polarity must be"),
        ({"confidence": "maybe"}, "confidence must be"),
        ({"sensitivity": "secret"}, "sensitivity must be"),
        ({"status": "done"}, "status must be"),
        ({"question_id": "Q99"}, "unknown question_id"),
        ({"week": "2026-43"}, "2026-W43"),
        ({"context": "  "}, "context is empty"),
        ({"project": ""}, "project is empty"),
    ],
)
def test_validate_rejects(over, fragment):
    errs = errors_of(card(**over))
    assert any(fragment in e for e in errs), errs


def test_validate_requires_fields_and_unique_ids():
    c = card()
    del c["project"]
    assert any("missing project" in e for e in errors_of(c))
    assert any("duplicate card_id" in e for e in errors_of(card(), card()))


def test_none_card_and_allowed_polarity_pass():
    assert errors_of(card(claim="該当なし: 今週は中断が無かった")) == []
    q4 = card(question_id="Q4", polarity="proposal", card_id="2026-W43/Q4/y.toyota/001")
    assert errors_of(q4) == []


def test_validate_warns_on_new_tags_and_volume():
    _, warnings = cards.validate([card(tags=["prompt", "newtag"])], CATALOG)
    assert any("newtag" in w for w in warnings)
    many = [card(card_id=f"2026-W43/Q2/y.toyota/{i:03d}") for i in range(1, 5)]
    errs, warnings = cards.validate(many, CATALOG)
    assert errs == []
    assert any("Q2: 4 cards" in w for w in warnings)


def test_validate_cli_exit_codes(tmp_path):
    good = tmp_path / "good.jsonl"
    good.write_text(json.dumps(card(), ensure_ascii=False) + "\n", encoding="utf-8")
    assert run("validate", good).returncode == 0
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps(card(claim="短い"), ensure_ascii=False) + "\n", encoding="utf-8")
    r = run("validate", bad)
    assert r.returncode == 1 and "min 20" in r.stdout
    broken = tmp_path / "broken.jsonl"
    broken.write_text("{\n", encoding="utf-8")
    r = run("validate", broken)
    assert r.returncode == 2 and "not valid JSON" in r.stderr


# ---- render / parse ----


def sample_cards():
    return [
        card(
            card_id="2026-W43/P1/y.toyota/001",
            question_id="P1",
            polarity="fact",
            claim="ai_development_tools: ナレッジカードのスキルを実装中",
            context="- 設計書を書いた\n- cards.py を実装した",
            evidence=[{"type": "commit", "ref": "s2@2026-10-20T03:00", "excerpt": "feat: cards.py を追加"}],
            tags=[],
        ),
        card(),
        card(
            card_id="2026-W43/Q3/y.toyota/001",
            question_id="Q3",
            polarity="proposal",
            claim="該当なし: 今週は新しい定型手順を作っていない",
            confidence="inferred",
            evidence=[{"type": "harness", "ref": "harness:commands/issue-impl", "excerpt": ""}],
            tags=["skill"],
        ),
    ]


def test_render_parse_round_trip():
    original = sample_cards()
    md = cards.render(original, CATALOG)
    assert "y.toyota@example.com" not in md
    assert "# ナレッジカード 2026-W43（10/19〜10/25）" in md
    assert "## Q2 言い直し・中断" in md
    assert cards.parse(md, copy.deepcopy(original)) == [cards.ordered(c) for c in original]


def test_parse_drops_deleted_sections_and_marked_cards():
    original = sample_cards()
    md = cards.render(original, CATALOG)
    md = md.replace("- 状態: draft\n- 極性: fact", "- 状態: dropped\n- 極性: fact")
    start = md.index("### 該当なし")
    md = md[:start]
    parsed = {c["card_id"]: c["status"] for c in cards.parse(md, original)}
    assert parsed == {
        "2026-W43/P1/y.toyota/001": "dropped",
        "2026-W43/Q2/y.toyota/001": "draft",
        "2026-W43/Q3/y.toyota/001": "dropped",
    }


def test_parse_applies_edits_and_numbers_new_cards():
    original = sample_cards()
    md = cards.render(original, CATALOG)
    md = md.replace("テストの範囲で 2 回言い直した", "テストの範囲を書かず 2 回言い直した")
    md = md.replace("- タグ: prompt, testing", "- タグ: prompt")
    md += (
        "\n### 依頼の最初に完了条件のテスト名を書くと言い直しが減った\n\n"
        "- 状態: approved\n- 極性: failed / 確度: inferred / 公開範囲: internal\n"
        "- プロジェクト: ai_development_tools\n- タグ: prompt\n\n手で足したカード。\n\n**根拠**\n\n"
        "- prompt `abc-2@2026-10-21T09:00`: テスト名を先に書いた\n"
    )
    parsed = cards.parse(md, original)
    edited = next(c for c in parsed if c["card_id"] == "2026-W43/Q2/y.toyota/001")
    assert edited["claim"] == "完了条件を書かずに依頼し、テストの範囲を書かず 2 回言い直した"
    assert edited["tags"] == ["prompt"]
    assert edited["author_email"] == "y.toyota@example.com"
    new = parsed[-1]
    assert new["card_id"] == "2026-W43/Q3/y.toyota/002"
    assert new["question_id"] == "Q3"
    assert new["status"] == "approved"
    assert new["author_email"] == "y.toyota@example.com"
    assert new["evidence"] == [{"type": "prompt", "ref": "abc-2@2026-10-21T09:00", "excerpt": "テスト名を先に書いた"}]


def test_parse_keeps_submitted_cards_when_removed():
    original = [card(status="submitted", notion_url="https://www.notion.so/x")]
    assert cards.parse("# empty\n", original)[0]["status"] == "submitted"


def test_render_parse_cli(tmp_path):
    src = tmp_path / "cards.jsonl"
    cards.write_cards(src, sample_cards())
    md = tmp_path / "cards-2026-W43.md"
    assert run("render", src, "--out", md).returncode == 0
    out = tmp_path / "back.jsonl"
    r = run("parse", md, "--base", src, "--out", out)
    assert r.returncode == 0, r.stderr
    assert cards.read_cards(out) == cards.read_cards(src)


# ---- dedupe / to-notion / mark-submitted ----


def test_dedupe_matches_normalized_claims():
    submitted = [{"key": cards.card_key(card(claim="完了条件を書かずに依頼し テストの範囲で2回言い直した。")),
                  "notion_url": "https://www.notion.so/p1"}]
    out, marked = cards.dedupe([card(), card(card_id="x", project="other")], submitted)
    assert marked == 1
    assert out[0]["status"] == "submitted" and out[0]["notion_url"] == "https://www.notion.so/p1"
    assert out[1]["status"] == "draft"


def test_to_notion_properties():
    long_card = card(context="CLAUDE.md の書き方を直す依頼で、完了条件を書かなかった。",
                     evidence=[{"type": "prompt", "ref": "a@1", "excerpt": "あ" * 120},
                               {"type": "memory", "ref": "memory:x/y", "excerpt": "い" * 120}])
    pages = cards.to_notion([long_card, card(card_id="d", status="dropped")], "https://www.notion.so/week", "user-1")
    assert len(pages) == 1
    props = pages[0]["properties"]
    assert props["カード"] == long_card["claim"]
    assert props["問い"] == "Q2"
    assert props["週"] == ["https://www.notion.so/week"]
    assert props["投稿者"] == ["user-1"]
    assert props["プロジェクト"] == ["ai_development_tools"]
    assert props["タグ"] == ["prompt", "testing"]
    assert len(props["根拠"]) == 241
    assert props["根拠参照"] == "a@1, memory:x/y"
    assert "author_email" not in json.dumps(pages)
    body = pages[0]["content"]
    assert body.startswith("`CLAUDE.md` の書き方を直す依頼で")  # context first, file names as code
    assert "<summary>記録の抜粋（2）</summary>\n\t- 依頼文: " in body
    assert "<summary>記録の場所（本人が見返す用）</summary>\n\t- `a@1`" in body
    me = cards.to_notion([card()], "u", "me")[0]["properties"]
    assert "投稿者" not in me


def test_mark_submitted_cli_records_and_dedupes(tmp_path):
    src = tmp_path / "cards.jsonl"
    cards.write_cards(src, [card(), card(card_id="2026-W43/Q2/y.toyota/002", claim="別の結論を書いたカードで二十文字を超える")])
    results = tmp_path / "results.json"
    results.write_text(json.dumps([{"card_id": "2026-W43/Q2/y.toyota/001", "notion_url": "https://www.notion.so/p1"}]))
    submitted = tmp_path / "submitted.jsonl"
    r = run("mark-submitted", src, "--submitted", submitted, "--results", results)
    assert r.returncode == 0, r.stderr
    rows = [json.loads(x) for x in submitted.read_text().splitlines()]
    assert rows[0]["card_id"] == "2026-W43/Q2/y.toyota/001"
    statuses = [c["status"] for c in cards.read_cards(src)]
    assert statuses == ["submitted", "draft"]

    again = tmp_path / "again.jsonl"
    cards.write_cards(again, [card(card_id="2026-W44/Q2/y.toyota/001")])
    assert "1 card(s) were already submitted" in run("dedupe", again, "--submitted", submitted).stdout
    assert cards.read_cards(again)[0]["status"] == "submitted"


# ---- options (multi_select choices missing in Notion) ----

SCHEMA_STATE = {
    "name": "ナレッジカード",
    "schema": {
        "プロジェクト": {"type": "multi_select", "options": [
            {"name": "その他", "color": "gray"}, {"name": "akita-shoten", "color": "orange"}]},
        "タグ": {"type": "multi_select", "options": [{"name": "prompt", "color": "blue"}, {"name": "git", "color": "gray"}]},
    },
}


def test_missing_options_and_alter_statements_keep_existing():
    cs = [card(project="akita-shoten", tags=["prompt"]), card(card_id="x", project="o'brien-app", tags=["git", "ci"]),
          card(card_id="d", project="dropped-app", status="dropped")]
    result = cards.missing_options(cs, SCHEMA_STATE)
    assert result["missing"] == {"プロジェクト": ["o'brien-app"], "タグ": ["ci"]}
    assert result["statements"] == [
        "ALTER COLUMN \"プロジェクト\" SET MULTI_SELECT('その他':gray, 'akita-shoten':orange, 'o''brien-app':default)",
        "ALTER COLUMN \"タグ\" SET MULTI_SELECT('prompt':blue, 'git':gray, 'ci':default)",
    ]


def test_no_missing_options_means_no_statements():
    result = cards.missing_options([card(project="akita-shoten", tags=["prompt"])], SCHEMA_STATE)
    assert result == {"missing": {"プロジェクト": [], "タグ": []}, "statements": []}


def test_options_cli_reads_raw_fetch_output(tmp_path):
    src = tmp_path / "cards.jsonl"
    cards.write_cards(src, [card(project="new-app", tags=["prompt"])])
    fetched = tmp_path / "schema.txt"
    fetched.write_text("<data-source>\n<data-source-state>\n" + json.dumps(SCHEMA_STATE, ensure_ascii=False)
                       + "\n</data-source-state>\n</data-source>", encoding="utf-8")
    r = run("options", src, "--schema", fetched)
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["missing"]["プロジェクト"] == ["new-app"]
    assert out["statements"][0].endswith("'new-app':default)")
    bad = tmp_path / "bad.txt"
    bad.write_text("no schema here", encoding="utf-8")
    assert run("options", src, "--schema", bad).returncode == 2


# ---- confidential topics ----


def test_validate_rejects_cards_on_confidential_topics():
    sys.path.insert(0, str(SCRIPTS))
    import topics as topics_mod  # noqa: E402

    loaded = topics_mod.load_topics([topics_mod.DEFAULT_FILE])
    bad = card(context="経営会議の資料づくりで、数字の確認を先に頼んだ。")
    errors, _ = cards.validate([bad], CATALOG, loaded)
    assert any("confidential topic" in e for e in errors)
    bad2 = card(evidence=[{"type": "prompt", "ref": "a@1", "excerpt": "部下の人事評価を下書きして"}])
    assert any("confidential topic" in e for e in cards.validate([bad2], CATALOG, loaded)[0])
    assert cards.validate([card()], CATALOG, loaded) == ([], [])
    dropped = card(status="dropped", context="経営会議の資料")
    assert cards.validate([dropped], CATALOG, loaded)[0] == []


def test_validate_cli_uses_default_topics(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps(card(claim="取締役会の資料を一発で作れた依頼の書き方がある"), ensure_ascii=False) + "\n", encoding="utf-8")
    r = run("validate", bad)
    assert r.returncode == 1 and "confidential topic" in r.stdout


def test_review_words_fail_until_allowed_but_strong_words_never_pass(tmp_path):
    src = tmp_path / "cards.jsonl"
    cards.write_cards(src, [card(context="顧客アプリの退職者処理を非同期にした依頼で、完了条件を書かなかった。")])
    r = run("validate", src)
    assert r.returncode == 1 and "--allow-term '退職'" in r.stdout
    assert run("validate", src, "--allow-term", "退職").returncode == 0
    cards.write_cards(src, [card(context="取締役会の資料の依頼で、完了条件を書かなかった。")])
    assert run("validate", src, "--allow-term", "取締役").returncode == 1


def test_long_context_warns():
    _, warnings = cards.validate([card(context="あ" * 161)], CATALOG)
    assert any("context is 161 chars" in w for w in warnings)


def test_workdir_cards_creates_run_and_state_outside_cwd(tmp_path):
    root = tmp_path / "home" / "knowledge-cards"
    out = cards.workdir("cards", "2026-W43", root, tmp_path / "repo")
    assert out["run"] == str(root / "runs" / "2026-W43")
    assert out["work"] == str(root / "runs" / "2026-W43" / ".work")
    assert out["state"] == str(root / "state")
    assert Path(out["work"]).is_dir() and Path(out["state"]).is_dir()
    assert "legacy" not in out
    assert not (tmp_path / "repo").exists()


def test_workdir_synthesis_and_tips(tmp_path):
    root = tmp_path / "kc"
    syn = cards.workdir("synthesis", "2026-W41", root, tmp_path)
    assert syn["work"] == str(root / "synthesis" / "2026-W41" / ".work")
    assert "state" not in syn
    tips = cards.workdir("tips", None, root, tmp_path)
    assert tips == {"root": str(root), "work": str(root / "tips" / ".work")}
    with pytest.raises(cards.InputError):
        cards.workdir("cards", None, root, tmp_path)


def test_workdir_merges_legacy_state_without_overwriting(tmp_path):
    root, repo = tmp_path / "kc", tmp_path / "repo"
    legacy = repo / "cards" / ".work"
    legacy.mkdir(parents=True)
    (legacy / "notion-user.json").write_text('{"user_id": "old"}', encoding="utf-8")
    (legacy / "allow.txt").write_text("foo\n", encoding="utf-8")
    (legacy / "submitted.jsonl").write_text('{"key": "a"}\n{"key": "b"}\n', encoding="utf-8")
    state = root / "state"
    state.mkdir(parents=True)
    (state / "notion-user.json").write_text('{"user_id": "new"}', encoding="utf-8")
    (state / "submitted.jsonl").write_text('{"key": "a"}\n', encoding="utf-8")
    out = cards.workdir("cards", "2026-W43", root, repo)
    assert out["legacy"] == str(legacy)
    assert out["migrated"] == ["allow.txt", "submitted.jsonl (+1)"]
    assert json.loads((state / "notion-user.json").read_text())["user_id"] == "new"
    assert [r["key"] for r in cards.read_submitted(state / "submitted.jsonl")] == ["a", "b"]
    assert cards.workdir("cards", "2026-W43", root, repo)["migrated"] == []
    assert legacy.is_dir()


def test_cleanup_deletes_only_run_directories(tmp_path):
    root = tmp_path / "kc"
    run = Path(cards.workdir("cards", "2026-W43", root, tmp_path)["run"])
    (run / ".work" / "sessions.json").write_text("{}", encoding="utf-8")
    syn = Path(cards.workdir("synthesis", "2026-W43", root, tmp_path)["run"])
    assert cards.cleanup(run, root) == run.resolve()
    assert not run.exists()
    cards.cleanup(syn, root)
    assert not syn.exists()
    assert (root / "state").is_dir()
    cards.cleanup(run, root)  # already gone: no error

    for bad in (root, root / "state", root / "runs", tmp_path / "cards", root / "runs" / "2026-W43" / ".work",
                root / "runs" / ".." / "state", root / "tips" / "2026-W43", tmp_path / "other" / "runs" / "2026-W43"):
        with pytest.raises(cards.InputError):
            cards.cleanup(bad, root)
    assert (root / "state").is_dir()


def test_cleanup_refuses_symlinks(tmp_path):
    root = tmp_path / "kc"
    victim = tmp_path / "repo"
    victim.mkdir()
    (root / "runs").mkdir(parents=True)
    link = root / "runs" / "2026-W43"
    link.symlink_to(victim)
    with pytest.raises(cards.InputError):
        cards.cleanup(link, root)
    assert victim.is_dir()


def test_workdir_cleanup_cli(tmp_path):
    root = tmp_path / "kc"
    res = subprocess.run([sys.executable, "-I", str(CARDS), "workdir", "--kind", "cards", "--week", "2026-W43",
                          "--root", str(root)], capture_output=True, text=True, cwd=tmp_path)
    assert res.returncode == 0, res.stderr
    run = json.loads(res.stdout)["run"]
    res = subprocess.run([sys.executable, "-I", str(CARDS), "cleanup", str(tmp_path), "--root", str(root)],
                         capture_output=True, text=True)
    assert res.returncode == 2 and "refusing" in res.stderr
    res = subprocess.run([sys.executable, "-I", str(CARDS), "cleanup", run, "--root", str(root)],
                         capture_output=True, text=True)
    assert res.returncode == 0 and not Path(run).exists()


def test_workdir_directories_are_private(tmp_path):
    root = tmp_path / "home" / ".claude" / "knowledge-cards"
    out = cards.workdir("cards", "2026-W43", root, tmp_path)
    cards.workdir("tips", None, root, tmp_path)
    for path in (root, root / "runs", Path(out["run"]), Path(out["work"]), Path(out["state"]), root / "tips", root / "tips" / ".work"):
        assert path.stat().st_mode & 0o077 == 0, path
