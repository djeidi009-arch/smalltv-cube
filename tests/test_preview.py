from cube.__main__ import main


def test_preview_writes_every_screen(tmp_path):
    main(["preview", str(tmp_path)])
    names = {p.stem for p in tmp_path.glob("*.png")}
    assert {"limits-empty", "limits-filled", "limits-partial", "limits-waiting",
            "card-figma", "card-telegram", "card-claude_limit", "card-claude_waiting",
            "card-summary"} <= names
    assert (tmp_path / "card-telegram-intro.gif").stat().st_size > 0
