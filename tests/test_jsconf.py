import pytest

from .utils import srcdir


@pytest.mark.sphinx(
    srcdir=srcdir,
    confoverrides={
        'hoverxref_tooltip_lazy': True,
    },
)
def test_lazy_tooltips(app, status, warning):
    app.build()
    path = app.outdir / '_static/js/hoverxref.js'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        ".one('mouseenter click touchstart tap', function(event) {",
        ".tooltipster('open');",
    ]

    for chunk in chunks:
        assert chunk in content

    ignored_chunks = [
        ".each(function () { $(this).removeAttr('title') });",
    ]
    for chunk in ignored_chunks:
        assert chunk not in content


@pytest.mark.sphinx(
    srcdir=srcdir,
    confoverrides={
        'hoverxref_tooltip_lazy': False,
    },
)
def test_nonlazy_strips_title_from_internal_tooltip_links(app, status, warning):
    app.build()
    path = app.outdir / '_static/js/hoverxref.js'
    assert path.exists() is True
    content = open(path).read()

    # The non-lazy branch must strip title= from internal tooltip links
    # (.hxr-hoverxref.hxr-tooltip) to avoid double tooltips (browser native +
    # Tooltipster).  External links are handled separately and must still work.
    assert ".hxr-hoverxref.hxr-tooltip" in content
    assert "removeAttr('title')" in content

    # Verify that removeAttr('title') is applied to the tooltip selector,
    # not only to .external links.
    import re
    # Find all selectors that call removeAttr('title')
    pattern = r"\$\(['\"]([^'\"]+)['\"]\)\.each\(function\s*\(\)\s*\{\s*\$\(this\)\.removeAttr\('title'\)\s*\}\)"
    matches = re.findall(pattern, content)
    selectors = [m for m in matches]

    # Must contain both .external and .hxr-hoverxref.hxr-tooltip selectors
    assert any('.hxr-hoverxref.external' in s for s in selectors), (
        f"Expected .hxr-hoverxref.external selector in {selectors}"
    )
    assert any('.hxr-hoverxref.hxr-tooltip' in s for s in selectors), (
        f"Expected .hxr-hoverxref.hxr-tooltip selector in {selectors}"
    )


@pytest.mark.sphinx(
    srcdir=srcdir,
)
def test_lazy_tooltips_notlazy(app, status, warning):
    app.build()
    path = app.outdir / '_static/js/hoverxref.js'
    assert path.exists() is True
    content = open(path).read()

    chunks = [
        ".each(function () { $(this).removeAttr('title') });",
    ]

    for chunk in chunks:
        assert chunk in content

    ignored_chunks = [
        ".one('mouseenter click touchstart tap', function(event) {",
        ".tooltipster('open');",
    ]
    for chunk in ignored_chunks:
        assert chunk not in content
