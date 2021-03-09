# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Test Invenio Assets module."""

from __future__ import absolute_import, print_function

from mock import patch
from pkg_resources import EntryPoint
from webassets import Bundle

from invenio_assets import InvenioAssets


class MockEntryPoint(EntryPoint):
    """Mocking of entrypoint."""

    def load(self):
        """Mock load entry point."""
        return Bundle(self.name)


def _mock_entry_points(name):
    data = {
        'invenio_assets.bundles': [MockEntryPoint('demo.bundle0',
                                                  'demo.bundle0'),
                                   MockEntryPoint('demo.bundle1',
                                                  'demo.bundle1')],
    }
    names = data.keys() if name is None else [name]
    for key in names:
        for entry_point in data[key]:
            yield entry_point


def test_version():
    """Test version import."""
    from invenio_assets import __version__
    assert __version__


def test_init(app):
    """Test module initialization."""
    InvenioAssets(app)
    assets = app.extensions['invenio-assets']
    assert assets.env
    assert assets.collect
    assert app.config['REQUIREJS_BASEURL'] == app.static_folder
    assert app.config['COLLECT_STATIC_ROOT'] == app.static_folder


def test_init_post(app):
    """Test module initialization using init_app."""
    assets = InvenioAssets()
    assert assets.env
    assert assets.collect
    assert 'REQUIREJS_BASEURL' not in app.config
    assert 'COLLECT_STATIC_ROOT' not in app.config
    assets.init_app(app)
    assert 'REQUIREJS_BASEURL' in app.config
    assert 'COLLECT_STATIC_ROOT' in app.config


def test_init_cli(app):
    """Test cli registration."""
    from flask.cli import cli
    cli._load_plugin_commands()
    assert 'assets' in cli.commands
    assert 'collect' in cli.commands
    assert 'npm' in cli.commands


def test_assets_usage(app):
    """Test assets usage."""
    class Ext(object):
        def __init__(self, app):
            assets = app.extensions['invenio-assets']
            assets.env.register('testbundle', Bundle())

    assets = InvenioAssets(app)
    Ext(app)
    assert len(assets.env) == 1


@patch('pkg_resources.iter_entry_points', _mock_entry_points)
def test_assets_usage_entrypoints(app):
    """Test of entrypoints using mocking."""
    assets = InvenioAssets(app)
    assert len(assets.env) == 2
