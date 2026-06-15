import logging
from types import SimpleNamespace

import pytest
from unittest import mock

from sphinx.events import EventListener
from sphinx.ext.intersphinx import missing_reference as intersphinx_missing_reference
from hoverxref.extension import deprecated_configs_warning, missing_reference

from .utils import srcdir


def _make_app(old_value, new_value, default='/_'):
    """Build a minimal fake app for deprecated_configs_warning."""
    config = SimpleNamespace(
        hoverxref_tooltip_api_host=old_value,
        hoverxref_api_host=new_value,
        values={
            'hoverxref_tooltip_api_host': SimpleNamespace(default=default),
            'hoverxref_api_host': SimpleNamespace(default=default),
        },
    )
    return SimpleNamespace(config=config)


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


_SPHINX_LOGGER_NAME = 'sphinx.hoverxref.extension'


@pytest.fixture()
def _caplog_sphinx(caplog):
    """Attach caplog handler to the Sphinx-namespaced logger so records are captured
    even when the ``sphinx`` logger has ``propagate=False`` (set by Sphinx's own
    logging setup during earlier tests)."""
    target = logging.getLogger(_SPHINX_LOGGER_NAME)
    target.addHandler(caplog.handler)
    caplog.handler.setLevel(logging.WARNING)
    yield caplog
    target.removeHandler(caplog.handler)


def test_deprecated_tooltip_api_host_migrates_when_new_is_default(_caplog_sphinx):
    """Old config set, new config at default: warn and migrate old value."""
    caplog = _caplog_sphinx
    app = _make_app(old_value='https://custom.host', new_value='/_')

    deprecated_configs_warning(app, None)

    assert '"hoverxref_tooltip_api_host" is deprecated' in caplog.text
    assert app.config.hoverxref_api_host == 'https://custom.host'


def test_deprecated_does_not_override_explicit_api_host(_caplog_sphinx):
    """Both configs set to non-default: warn but do not overwrite hoverxref_api_host."""
    caplog = _caplog_sphinx
    app = _make_app(
        old_value='https://old.host',
        new_value='https://new.host',
    )

    deprecated_configs_warning(app, None)

    assert '"hoverxref_tooltip_api_host" is deprecated' in caplog.text
    # The new explicit value must NOT be overwritten by the old one
    assert app.config.hoverxref_api_host == 'https://new.host'
