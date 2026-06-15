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


def test_missing_reference_classes_none_safe():
    """
    Test ``missing_reference`` does not crash when ``newnode.get('classes')``
    returns ``None`` and does not duplicate classes when they already exist.
    """
    from docutils import nodes
    from hoverxref.extension import CSS_DEFAULT_CLASS, CSS_CLASSES

    # --- Case 1: classes is None ---
    app = mock.MagicMock()
    app.config.hoverxref_intersphinx = ['python']
    app.config.extensions = ['sphinx.ext.intersphinx']
    app.config.hoverxref_intersphinx_types = {}
    app.config.hoverxref_default_type = 'tooltip'

    env = mock.MagicMock()

    node = nodes.reference()
    node['refdomain'] = 'std'
    node['reftarget'] = 'python:some-label'
    node['reftype'] = 'ref'

    contnode = nodes.reference()

    # The newnode returned by sphinx_missing_reference has classes=None
    newnode_no_classes = nodes.reference()
    newnode_no_classes.replace_attr('classes', None)

    with mock.patch(
        'hoverxref.extension.sphinx_missing_reference',
        return_value=newnode_no_classes,
    ):
        result = missing_reference(app, env, node, contnode)

    assert result is not None
    assert CSS_DEFAULT_CLASS in result['classes']
    # No duplicates
    assert result['classes'].count(CSS_DEFAULT_CLASS) == 1

    # --- Case 2: classes already contains hxr-hoverxref ---
    node2 = nodes.reference()
    node2['refdomain'] = 'std'
    node2['reftarget'] = 'python:some-label'
    node2['reftype'] = 'ref'

    contnode2 = nodes.reference()

    newnode_with_classes = nodes.reference()
    newnode_with_classes['classes'] = [CSS_DEFAULT_CLASS]

    with mock.patch(
        'hoverxref.extension.sphinx_missing_reference',
        return_value=newnode_with_classes,
    ):
        result2 = missing_reference(app, env, node2, contnode2)

    assert result2 is not None
    # Must not duplicate CSS_DEFAULT_CLASS
    assert result2['classes'].count(CSS_DEFAULT_CLASS) == 1
    # Type class should still be added once
    tooltip_class = CSS_CLASSES['tooltip']
    assert result2['classes'].count(tooltip_class) == 1


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
