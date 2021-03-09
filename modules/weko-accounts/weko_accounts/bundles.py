# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Bundles for weko-index-tree."""

from flask_assets import Bundle
from invenio_assets_legacy import NpmBundle

embedded_wayf_custom = Bundle(
    'css/weko_accounts/wayf_custom.css',
    output="gen/weko_accounts_wayf_custom.%(version)s.css",
)

embedded_ds_P1_js = Bundle(
    'js/weko_accounts/embedded_ds.js',
    output="gen/weko_accounts_embedded_ds_1.%(version)s.js",
)

embedded_ds_P2_js = Bundle(
    'js/weko_accounts/embedded_ds_2.js',
    output="gen/weko_accounts_embedded_ds_2.%(version)s.js",
)

embedded_ds_multi_language_js = Bundle(
    'js/weko_accounts/change_translation_embedded.js',
    output="gen/weko_accounts_embedded_ds_multi_language.%(version)s.js",
)

suggest_js = NpmBundle(
    'js/weko_accounts/suggest.js',
    output="gen/weko_accounts_suggest.js",
)
