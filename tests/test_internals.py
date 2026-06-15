import pytest
from unittest import mock

from sphinx.events import EventListener
from sphinx.ext.intersphinx import missing_reference as intersphinx_missing_reference
from hoverxref.extension import missing_reference

from .utils import srcdir


@pytest.mark.sphinx(
    srcdir=srcdir,
    buildername='latex',
    confoverrides={
        'hoverxref_auto_ref': True,
    },
)
def test_dont_fail_non_html_builder(app, status, warning):
    """
    Test our resolver is not used by non-HTML builder.

    When running the build with ``latex`` as builder and
    ``hoverxref_auto_ref=True`` it should not fail with

    def _get_docpath(self, builder, docname):
        docpath = builder.get_outfilename(docname)
        AttributeError: 'LaTeXBuilder' object has no attribute 'get_outfilename'

    LaTeXBuilder should never use our resolver.
    """

    app.build()
    path = app.outdir / 'test.tex'
    assert path.exists() is True
    content = open(path).read()

    assert app.builder.format == 'latex'


@pytest.mark.sphinx(
    srcdir=srcdir,
    confoverrides={
        'html_theme': 'furo',
        'extensions': [
            'sphinx.ext.autosectionlabel',
            'hoverxref.extension',
        ],
    },
)
def test_setup_theme_furo(app, status, warning):
    """Test that Furo theme auto-configures hoverxref_modal_class and copies furo.css."""
    app.build()
    assert app.config.hoverxref_modal_class == 'body'

    css_path = app.outdir / '_static' / 'css' / 'furo.css'
    assert css_path.exists()

    index_html = (app.outdir / 'index.html').read_text(encoding='utf-8')
    assert 'furo.css' in index_html


@pytest.mark.sphinx(
    srcdir=srcdir,
    confoverrides={
        'hoverxref_domains': ['py'],
        'hoverxref_intersphinx': ['python'],
        'hoverxref_auto_ref': True,
        'extensions': [
            'sphinx.ext.intersphinx',
            'hoverxref.extension',
        ],
    },
)
def test_disconnect_intersphinx_listener(app, status, warning):
    """The ``missing-reference`` listener from ``sphinx.ext.intershinx`` should be dropped in favor of ours."""
    app.build()
    missing_reference_listeners = app.events.listeners['missing-reference']
    assert EventListener(id=mock.ANY, priority=mock.ANY, handler=intersphinx_missing_reference) not in missing_reference_listeners
    assert EventListener(id=mock.ANY, priority=mock.ANY, handler=missing_reference) in missing_reference_listeners
