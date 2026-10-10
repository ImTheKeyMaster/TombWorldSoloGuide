from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def roster_css():
    return CSS.split(
        "Experimental Deathwatch Roster Rail. Current UI is intentionally untouched.", 1
    )[1]


def test_release_is_v10088_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 88)
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")


def test_full_miniature_detail_rendering_is_restored():
    block = roster_css()
    image = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-image img{', 1
    )[1].split("}", 1)[0]
    assert "object-fit:contain" in image
    assert "object-position:center bottom" in image
    assert "max-height:180px" in image
    assert "max-height:none" not in image


def test_dialog_height_is_reserved_by_the_detail_panel_not_by_shrinking_the_portrait():
    block = roster_css()
    detail = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail{', 1
    )[1].split("}", 1)[0]
    assert "min-height:206px" in detail

    frame = block.split(
        'html[data-ui="tomb"] .experimental-roster-detail-image{', 1
    )[1].split("}", 1)[0]
    assert "align-self:stretch" in frame
    assert all(not declaration.strip().startswith("height:") for declaration in frame.split(";"))
