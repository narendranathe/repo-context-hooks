# Brand Assets

`repo-context-hooks-logo.svg` is the source of truth for the brand mark.

Regenerate the PNG after changing the SVG:

```powershell
inkscape assets/brand/repo-context-hooks-logo.svg --export-type=png --export-filename=assets/brand/repo-context-hooks-logo.png --export-width=512 --export-height=512
```

If Inkscape is unavailable, use another deterministic SVG renderer, then verify:

```powershell
python -m pytest -q tests/test_monitoring_surface.py::test_png_brand_logo_exists_and_has_expected_dimensions --basetemp .pytest-tmp
```
