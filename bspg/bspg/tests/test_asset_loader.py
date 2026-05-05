from bspg.gui.assets.asset_loader import AssetLoader


def test_asset_loader(tmp_path):
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "logo.png").write_text("dummy")

    al = AssetLoader(assets_root=assets)
    assert al.logo_path().exists()
    assert al.icon_path('logo.png').exists()
    assert al.exists('logo.png') is True
    assert 'logo.png' in al.load_logo()
