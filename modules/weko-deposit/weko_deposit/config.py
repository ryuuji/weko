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

"""Configuration for weko-deposit."""

import copy

WEKO_BUCKET_QUOTA_SIZE = 50 * 1024 * 1024 * 1024  # 50 GB
"""Maximum quota per bucket."""

WEKO_MAX_FILE_SIZE = WEKO_BUCKET_QUOTA_SIZE
WEKO_MAX_FILE_SIZE_FOR_ES = 1 * 1024 * 1024  # 1MB
"""Maximum file size accepted."""

WEKO_MIMETYPE_WHITELIST_FOR_ES = [
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/pdf',
]

FILES_REST_STORAGE_FACTORY = 'weko_deposit.storage.pyfs_storage_factory'
"""Import path of factory used to create a storage instance."""

FILES_REST_UPLOAD_OWNER_FACTORIES = 'weko_deposit.serializer.file_uploaded_owner'
"""file update version"""

WEKO_DEPOSIT_ITEMS_CACHE_PREFIX = 'cache_itemsIndex_{pid_value}'
""" cache items prifix info"""

WEKO_DEPOSIT_ITEMS_CACHE_TTL = 300
""" cache default timeout 5 minutes"""

_PID = 'pid(depid,record_class="weko_deposit.api:WekoDeposit")'

#: Template for deposit list view.
DEPOSIT_SEARCH_API = '/api/deposits/items'

#: Template for deposit records API.
DEPOSIT_RECORDS_API = '/api/deposits/items/{pid_value}'
DEPOSIT_RECORDS_EDIT_API = '/api/deposits/redirect/{pid_value}'

DEPOSIT_REST_ENDPOINTS = dict(
    depid=dict(
        pid_type='depid',
        pid_minter='weko_deposit_minter',
        pid_fetcher='weko_deposit_fetcher',
        record_class='weko_deposit.api:WekoDeposit',
        record_serializers={
            'application/json': ('weko_records.serializers'
                                 ':deposit_json_v1_response'),
        },
        files_serializers={
            'application/json': ('invenio_deposit.serializers'
                                 ':json_v1_files_response'),
        },
        search_class='invenio_deposit.search:DepositSearch',
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/deposits/items',
        item_route='/deposits/items/<{0}:pid_value>'.format(_PID),
        file_list_route='/deposits/items/<{0}:pid_value>/files'.format(_PID),
        file_item_route='/deposits/items/<{0}:pid_value>/files/<path:key>'.format(
            _PID),
        default_media_type='application/json',
        links_factory_imp='weko_deposit.links:links_factory',
        max_result_window=10000,
        # create_permission_factory_imp='',
        # read_permission_factory_imp='',
        # update_permission_factory_imp='',
        # delete_permission_factory_imp='',
    )
)

# for redirect to next page(index select)
WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(DEPOSIT_REST_ENDPOINTS)
WEKO_DEPOSIT_REST_ENDPOINTS['depid']['rdc_route'] = '/deposits/redirect/<{0}:pid_value>'.format(
    _PID)
WEKO_DEPOSIT_REST_ENDPOINTS['depid']['pub_route'] = '/deposits/publish/<{0}:pid_value>'.format(
    _PID)

DEPOSIT_RECORDS_UI_ENDPOINTS = {
    'depid': {
        'pid_type': 'depid',
        'route': '/item/edit/<pid_value>',
        'template': 'weko_items_ui/edit.html',
        'record_class': 'weko_deposit.api:WekoDeposit',
        'view_imp': 'weko_items_ui.views.default_view_method',
        'permission_factory_imp': 'weko_items_ui.permissions:edit_permission_factory',
    },
    'iframe_depid': {
        'pid_type': 'depid',
        'route': '/item/iframe/edit/<pid_value>',
        'template': 'weko_items_ui/iframe/item_edit.html',
        'record_class': 'weko_deposit.api:WekoDeposit',
        'view_imp': 'weko_items_ui.views.default_view_method',
        'permission_factory_imp': 'weko_items_ui.permissions:edit_permission_factory',
    }
}

RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY = None
RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY = None
RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY = None
DEPOSIT_JSONSCHEMAS_PREFIX = ''

WEKO_DEPOSIT_SYS_CREATOR_KEY = {
    'creator_names': 'creatorNames',
    'creator_name': 'creatorName',
    'creator_lang': 'creatorNameLang',
    'family_names': 'familyNames',
    'family_name': 'familyName',
    'family_lang': 'familyNameLang',
    'given_names': 'givenNames',
    'given_name': 'givenName',
    'given_lang': 'givenNameLang',
    'alternative_names': 'creatorAlternatives',
    'alternative_name': 'creatorAlternative',
    'alternative_lang': 'creatorAlternativeLang',
    'identifiers': 'nameIdentifiers',
    'creator_mails': 'creatorMails',
    'affiliation_name_identifier_scheme': 'affiliationNameIdentifierScheme',
    'affiliation_name': 'affiliationName',
    'affiliation_lang': 'affiliationNameLang',
    'affiliation_name_identifier': 'affiliationNameIdentifier',
    'affiliation_name_identifier_URI': 'affiliationNameIdentifierURI',
    'creatorAffiliations': 'creatorAffiliations',
}
"""Key of Bibliographic information."""

WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY = [
    'bibliographicVolumeNumber',
    'bibliographicIssueNumber',
    'p.',
    'bibliographicNumberOfPages',
    'bibliographicIssueDates'
]
"""Key of Bibliographic information."""

WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_SYS_KEY = [
    'bibliographic_titles',
    'bibliographicPageEnd',
    'bibliographicIssueNumber',
    'bibliographicPageStart',
    'bibliographicVolumeNumber',
    'bibliographicNumberOfPages',
    'bibliographicIssueDates'
]
"""Bibliographic information sys key."""

WEKO_DEPOSIT_ES_PARSING_ERROR_PROCESS_ENABLE = True
"""Allow reindex data when catching parsing error from ElasticSearch."""

WEKO_DEPOSIT_ES_PARSING_ERROR_KEYWORD = 'ElasticsearchParseException'
"""Parsing error's Keyword in Elasticsearch exception info."""
