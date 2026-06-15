import logging
import pytest
from unittest import mock

from sphinx.events import EventListener
from sphinx.ext.intersphinx import missing_reference as intersphinx_missing_reference
from hoverxref.extension import missing_reference

from .utils import srcdir, customobjectsrcdir


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


@pytest.mark.sphinx(
    srcdir=customobjectsrcdir,
    confoverrides={
        'hoverxref_role_types': {'confval': 'not-a-real-type'},
    },
)
def test_invalid_hoverxref_role_type_falls_back(app, status, warning, caplog):
    """
    An invalid value in ``hoverxref_role_types`` must not crash the build.

    When a user configures ``hoverxref_role_types`` (or
    ``hoverxref_default_type``) with a value that is not a key in
    ``CSS_CLASSES`` (i.e. not ``'tooltip'`` or ``'modal'``), the extension
    should log a warning and gracefully fall back to a valid type so the
    HTML build completes without a ``KeyError``.
    """
    # Ensure caplog captures from the hoverxref loggers
    caplog.set_level(logging.WARNING, logger='hoverxref.domains')
    caplog.set_level(logging.WARNING, logger='hoverxref.extension')

    app.build()

    # The build must succeed and produce output
    path = app.outdir / 'index.html'
    assert path.exists() is True
    content = open(path).read()

    # A warning about the invalid type should have been logged.
    # Sphinx routes logger.warning through its own SphinxLoggerAdapter,
    # so we check both caplog records and the Sphinx ``warning`` fixture.
    warning_output = warning.getvalue()
    caplog_messages = [r.getMessage() for r in caplog.records]
    all_messages = warning_output + '\n'.join(caplog_messages)

    assert 'not-a-real-type' in all_messages, (
        'Expected a warning about invalid hoverxref type "not-a-real-type" '
        f'in warning output or caplog. Got:\n{all_messages}'
    )

    # The :confval: link should still carry the hoverxref classes,
    # falling back to 'tooltip' since the default is valid.
    assert 'hxr-hoverxref hxr-tooltip' in content, (
        'Expected :confval: link to have hxr-hoverxref hxr-tooltip classes '
        'after falling back from invalid type'
    )
