from hashlib import sha256
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "Assets" / "Images" / "TombUI" / "NecronActivation"

EXPECTED_SHA256 = {
    "canoptek-macrocyte-accelerator.webp": "bc33f936a169ee23fb3ed525dc15613cafc56db88d4a8a08ee0f9f1b24859d8d",
    "canoptek-macrocyte-reanimator.webp": "3b9c57c4f896ce8249b905548b6455b259d0e4360c8f7ba25b79b71164612565",
    "canoptek-macrocyte-warrior-1.webp": "23e7f6e146fb5e00504b8d5de4c2baa466b34394c949d62fca789a98ecacf699",
    "canoptek-macrocyte-warrior-2.webp": "66704a0d179bd30b3d19462860832ce56b39f678f8f221c4f5ea123825aa8009",
    "canoptek-macrocyte-warrior-3.webp": "3f7876268802442aa2790b704c4f5a73d8a459f65759a2d7d427d790096ef5e3",
    "canoptek-scarab-swarm.webp": "ab3b355d97fec8362c0c5b7ddfc34af906d49d9e421707c715035ba2fe0e5c73",
    "canoptek-tomb-crawler-1.webp": "be5683855171672ca153f8148a8b22dc91e2183a19811dc25668f89a24618820",
    "canoptek-tomb-crawler-2.webp": "f7e617108cff729eefe6be754299084764e90ff0a26dde9d988199e888408885",
    "geomancer.webp": "7954e22e29937a87a00cd955b9658cf49b32c5731311c458b6046d8931eb7996",
    "necron-warrior-gauss-flayer.webp": "aada3bde2a49dcd51dcbbf87713232716ae0478c0168a40825df303d72a744e7",
    "necron-warrior-gauss-reaper.webp": "77504024d95e0a2327d304c3702c72f5bc15c02ec08c4f6774a69d738ff35100",
}


def test_release_is_v100110_or_newer():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 110)


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


def test_supplied_necron_webps_have_384_square_pixels_and_alpha():
    for filename in EXPECTED_SHA256:
        data = (ASSET_ROOT / filename).read_bytes()
        assert data[0:4] == b"RIFF" and data[8:16] == b"WEBPVP8X", filename
        assert data[20] & 0x10, filename  # VP8X alpha flag
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        assert (width, height) == (384, 384), filename


def test_necron_portrait_urls_are_versioned_in_renderer_and_precache():
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    assert 'const versionedHref=`${href}?v=${APP_VERSION}`;' in app
    assert 'escapeHtml(versionedHref)' in app
    for filename in EXPECTED_SHA256:
        path = f'./Assets/Images/TombUI/NecronActivation/{filename}?v=${{APP_VERSION}}'
        assert path in worker, filename
