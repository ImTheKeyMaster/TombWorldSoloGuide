from hashlib import sha256
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "NecronActivation"

EXPECTED_SHA256 = {
    "canoptek-macrocyte-accelerator.webp": "db2f8126aa93ffba148106708ee753664ca2c5e0f9353ca7e1dc1541ba2878d6",
    "canoptek-macrocyte-reanimator.webp": "c68d107e4d4819c39372c08ded97622c22488082ef0a1eb1d0bcc3af9d68054e",
    "canoptek-macrocyte-warrior-1.webp": "59e3867d222501f1c143398f9f6679ce4c4b202b28291b41141c7f96ab286ed7",
    "canoptek-macrocyte-warrior-2.webp": "415ae6398da9e3c8635465bc9b3b5b9e4b7485a42b90623c37a145618ec682a5",
    "canoptek-macrocyte-warrior-3.webp": "b92de7f3fc91d59ed74db4d62f169c73d7d7134a66eb64155d6c5a1f2fd67622",
    "canoptek-scarab-swarm.webp": "65a313eac798effb343003c29ba2a5fd94bd560032af42ebda33f1bc33156d7c",
    "canoptek-tomb-crawler-1.webp": "de6ef9333892cbe932fee196ff073d4f56e64874e63828f6ab5a1619610ab87e",
    "canoptek-tomb-crawler-2.webp": "91d340a6eb3496396fa5b388bea39ad91f65fc53d38c3431e04658d121cb007d",
    "geomancer.webp": "a2a80a627d87362446476702960eda504556a281343eb50e83352b46b609b727",
    "necron-warrior-gauss-flayer.webp": "023862890742dc41d2cc9fcdb47b05eceb71d0512573443de46c2f763a9c8919",
    "necron-warrior-gauss-reaper.webp": "b4564ffbbf0d8bfa88088035e3d8663bfb812d1a38b1f34942779ba94564a0a8",
}


def test_release_is_v100109_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 109)


def test_exact_supplied_green_portrait_assets_are_committed():
    for filename, expected in EXPECTED_SHA256.items():
        data = (ASSET_ROOT / filename).read_bytes()
        assert sha256(data).hexdigest() == expected, filename


def test_necron_portraits_are_still_direct_rendered_without_runtime_recoloring():
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    start = app.index("function experimentalNecronPortraitSvg")
    end = app.index("function experimentalNecronPortraitMarkup", start)
    source = app[start:end]

    assert '<image href="' in source
    assert "<filter" not in source
    assert "feColorMatrix" not in source
    assert "feComponentTransfer" not in source
    assert "feConvolveMatrix" not in source
