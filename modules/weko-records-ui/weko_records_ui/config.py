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

"""Configuration for weko-records-ui."""
import os

from flask_babelex import lazy_gettext as _
from invenio_records_rest.utils import allow_all

from .views import blueprint

WEKO_RECORDS_UI_DETAIL_TEMPLATE = 'weko_records_ui/detail.html'
WEKO_RECORDS_UI_BASE_TEMPLATE = 'weko_theme/page.html'

WEKO_PERMISSION_REQUIRED_TEMPLATE = 'weko_workflow/permission_required.html'

WEKO_PERMISSION_ROLE_USER = ('System Administrator',
                             'Repository Administrator',
                             'Contributor',
                             'General',
                             'Community Administrator')

WEKO_PERMISSION_SUPER_ROLE_USER = ('System Administrator',
                                   'Repository Administrator')

WEKO_PERMISSION_ROLE_COMMUNITY = 'Community Administrator'

WEKO_PERMISSION_ROLE_GENERAL = 'General'

WEKO_RECORDS_UI_BULK_UPDATE_FIELDS = {
    'fields': [{'id': '1', 'name': 'Access Type'},
               {'id': '2', 'name': 'Licence'}]
}

ADMIN_SET_ITEM_TEMPLATE = 'weko_records_ui/admin/item_setting.html'
# author setting page template

WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE = 'weko_records_ui/admin/pdfcoverpage.html'
# pdfcoverpage templates

INSTITUTION_NAME_SETTING_TEMPLATE = 'weko_records_ui/admin/' \
                                    'institution_name_setting.html'
# institution name setting page template

ITEM_SEARCH_FLG = 'name'
# setting author name search type: name or id

EMAIL_DISPLAY_FLG = True
# setting the email of author if display

OPEN_DATE_DISPLAY_FLG = True
OPEN_DATE_DISPLAY_VALUE = '1'
OPEN_DATE_HIDE_VALUE = '0'
# setting the release date if display

# CSL Citation Formatter
# ======================
#: Styles Endpoint for CSL
CSL_STYLES_API_ENDPOINT = '/api/csl/styles'

#: Records Endpoint for CSL
CSL_RECORDS_API_ENDPOINT = '/api/record/cites/'

#: Template dirrectory for CSL
CSL_JSTEMPLATE_DIR = 'node_modules/invenio-csl-js/dist/templates/'

#: Template for CSL citation result
CSL_JSTEMPLATE_CITEPROC = 'template/weko_records_ui/invenio_csl/citeproc.html'

#: Template for CSL citation list item
CSL_JSTEMPLATE_LIST_ITEM = 'template/weko_records_ui/invenio_csl/item.html'

#: Template for CSL error
CSL_JSTEMPLATE_ERROR = os.path.join(CSL_JSTEMPLATE_DIR, 'error.html')

#: Template for CSL loading
CSL_JSTEMPLATE_LOADING = os.path.join(CSL_JSTEMPLATE_DIR, 'loading.html')

#: Template for CSL typeahead
CSL_JSTEMPLATE_TYPEAHEAD = os.path.join(CSL_JSTEMPLATE_DIR, 'typeahead.html')

RECORDS_UI_ENDPOINTS = dict(
    recid=dict(
        pid_type='recid',
        route='/records/<pid_value>',
        view_imp='weko_records_ui.views.default_view_method',
        template='weko_records_ui/detail.html',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
        # read_permission_factory_imp=allow_all,
        # record_serializers={
        #     'text/x-bibliography': ('weko_records.serializers',
        #         ':citeproc_v1_response'),
        # }
    ),
    recid_export=dict(
        pid_type='recid',
        route='/records/<pid_value>/export/<format>',
        view_imp='weko_records_ui.views.export',
        template='weko_records_ui/export.html',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_files=dict(
        pid_type='recid',
        route='/record/<pid_value>/files/<path:filename>',
        view_imp='weko_records_ui.fd.file_download_ui',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_file_details=dict(
        pid_type='recid',
        route='/records/<pid_value>/file_details/<path:filename>',
        view_imp='weko_records_ui.views.default_view_method',
        template='weko_records_ui/file_details.html',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_file_preview=dict(
        pid_type='recid',
        route='/record/<pid_value>/file_preview/<path:filename>',
        view_imp='weko_records_ui.fd.file_preview_ui',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_preview=dict(
        pid_type='recid',
        route='/record/<pid_value>/preview/<path:filename>',
        view_imp='weko_records_ui.preview.preview',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_publish=dict(
        pid_type='recid',
        route='/record/<pid_value>/publish',
        view_imp='weko_records_ui.views.publish',
        template='weko_records_ui/detail.html',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_items_ui.permissions'
                               ':edit_permission_factory',
        methods=['POST'],
    ),
)

RECORDS_UI_EXPORT_FORMATS = {
    'recid': {
        # 'junii2': dict(
        #     title='junii2',
        #     serializer='weko_schema_ui.serializers.WekoCommonSchema',
        #     order=1,
        # ),
        'jpcoar_1.0': dict(
            title='JPCOAR',
            serializer='weko_schema_ui.serializers.WekoCommonSchema',
            order=2,
        ),
        'oai_dc': dict(
            title='DublinCore',
            serializer='weko_schema_ui.serializers.WekoCommonSchema',
            order=3,
        ),
        'json': dict(
            title='JSON',
            serializer='invenio_records_rest.serializers.json_v1',
            order=4,
        ),
        'bibtex': dict(
            title='BIBTEX',
            serializer='weko_schema_ui.serializers.BibTexSerializer',
            order=5,
        ),
        'ddi': dict(
            title='DDI',
            serializer='weko_schema_ui.serializers.WekoCommonSchema',
            order=6,
        ),
    }
}

WEKO_RECORDS_UI_CITES_REST_ENDPOINTS = {
    'depid': {
        'pid_type': 'depid',
        'pid_minter': 'deposit',
        'pid_fetcher': 'deposit',
        'record_class': 'weko_deposit.api:WekoRecord',
        'record_serializers': {
            'text/x-bibliography': ('weko_records.serializers',
                                    ':citeproc_v1_response'),
        },
        'cites_route': '/record/cites/<int:pid_value>',
        'default_media_type': 'application/json',
        'max_result_window': 10000,
    },
}

OAISERVER_METADATA_FORMATS = {
    'junii2': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'junii2',
            }
        ),
        'schema': 'http://irdb.nii.ac.jp/oai/junii2-3-1.xsd',
        'namespace': 'http://irdb.nii.ac.jp/oai',
    },
    'jpcoar_1.0': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'jpcoar',
            }
        ),
        'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/',
        'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd',
    },
    'oai_dc': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'oai_dc',
            }
        ),
        'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
    },
    'ddi': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'ddi',
            }
        ),
        'namespace': 'ddi:codebook:2_5',
        'schema': 'https://ddialliance.org/Specification'
                  '/DDI-Codebook/2.5/XMLSchema/codebook.xsd',
    },
}

URL_OA_POLICY_HEIGHT = 7  # height of the URL & OA-policy
# title_h = 8  # height of the title
TITLE_HEIGHT = 8  # height of the title
# header_h = 20  # height of the header cell
HEADER_HEIGHT = 20  # height of the header cell
# footer_h = 4  # height of the footer cell
FOOTER_HEIGHT = 4  # height of the footer cell
# meta_h = 9  # height of the metadata cell
METADATA_HEIGHT = 9

# Path to the JPAexg font file
JPAEXG_TTF_FILEPATH = blueprint.root_path + "/fonts/ipaexg00201/ipaexg.ttf"

# Path to the JPAexm font file
JPAEXM_TTF_FILEPATH = blueprint.root_path + "/fonts/ipaexm00201/ipaexm.ttf"

PDF_COVERPAGE_LANG_FILEPATH = blueprint.root_path + "/translations/"

PDF_COVERPAGE_LANG_FILENAME = "/pdf_coverpage.json"

WEKO_RECORDS_UI_DEFAULT_MAX_WIDTH_THUMBNAIL = 100
"""Default max width of thumbnail."""

WEKO_RECORDS_UI_DOWNLOAD_DAYS = 7
"""Default download period."""

WEKO_RECORDS_UI_USAGE_APPLICATION_WORKFLOW_DICT = []
"""Mapping from role + data type => Usage application workflow."""

WEKO_RECORDS_UI_LICENSE_ICON_LOCATION = "static/images/default"
"""Location of list license's icons."""

WEKO_RECORDS_UI_LICENSE_ICON_PDF_LOCATION = "static/images/creative_commons"
"""Location of list license's icons for PDF."""

WEKO_RECORDS_UI_LICENSE_DICT = [
    {
        'name': _('write your own license'),
        'value': 'license_free',
    },
    # version 0
    {
        'name': _(
            'Creative Commons CC0 1.0 Universal Public Domain Designation'),
        'code': 'CC0',
        'href_ja': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja',
        'href_default': 'https://creativecommons.org/publicdomain/zero/1.0/',
        'value': 'license_12',
        'src': '88x31(0).png',
        'src_pdf': 'cc-0.png',
        'href_pdf': 'https://creativecommons.org/publicdomain/zero/1.0/'
                    'deed.ja',
        'txt': 'This work is licensed under a Public Domain Dedication '
               'International License.'
    },
    # version 3.0
    {
        'name': _('Creative Commons Attribution 3.0 Unported (CC BY 3.0)'),
        'code': 'CC BY 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by/3.0/',
        'value': 'license_6',
        'src': '88x31(1).png',
        'src_pdf': 'by.png',
        'href_pdf': 'http://creativecommons.org/licenses/by/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               ' 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-ShareAlike 3.0 Unported '
            '(CC BY-SA 3.0)'),
        'code': 'CC BY-SA 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-sa/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-sa/3.0/',
        'value': 'license_7',
        'src': '88x31(2).png',
        'src_pdf': 'by-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-sa/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-ShareAlike 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'),
        'code': 'CC BY-ND 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nd/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nd/3.0/',
        'value': 'license_8',
        'src': '88x31(3).png',
        'src_pdf': 'by-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nd/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NoDerivatives 3.0 International License.'

    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial 3.0 Unported'
            ' (CC BY-NC 3.0)'),
        'code': 'CC BY-NC 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc/3.0/',
        'value': 'license_9',
        'src': '88x31(4).png',
        'src_pdf': 'by-nc.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 '
            'Unported (CC BY-NC-SA 3.0)'),
        'code': 'CC BY-NC-SA 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
        'value': 'license_10',
        'src': '88x31(5).png',
        'src_pdf': 'by-nc-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-NoDerivs '
            '3.0 Unported (CC BY-NC-ND 3.0)'),
        'code': 'CC BY-NC-ND 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
        'value': 'license_11',
        'src': '88x31(6).png',
        'src_pdf': 'by-nc-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 3.0 International License.'
    },
    # version 4.0
    {
        'name': _('Creative Commons Attribution 4.0 International (CC BY 4.0)'),
        'code': 'CC BY 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by/4.0/',
        'value': 'license_0',
        'src': '88x31(1).png',
        'src_pdf': 'by.png',
        'href_pdf': 'http://creativecommons.org/licenses/by/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               ' 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-ShareAlike 4.0 International '
            '(CC BY-SA 4.0)'),
        'code': 'CC BY-SA 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'value': 'license_1',
        'src': '88x31(2).png',
        'src_pdf': 'by-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-sa/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-ShareAlike 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NoDerivatives 4.0 International '
            '(CC BY-ND 4.0)'),
        'code': 'CC BY-ND 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nd/4.0/',
        'value': 'license_2',
        'src': '88x31(3).png',
        'src_pdf': 'by-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nd/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NoDerivatives 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial 4.0 International'
            ' (CC BY-NC 4.0)'),
        'code': 'CC BY-NC 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'value': 'license_3',
        'src': '88x31(4).png',
        'src_pdf': 'by-nc.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-ShareAlike 4.0'
            ' International (CC BY-NC-SA 4.0)'),
        'code': 'CC BY-NC-SA 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'value': 'license_4',
        'src': '88x31(5).png',
        'src_pdf': 'by-nc-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 '
            'International (CC BY-NC-ND 4.0)'),
        'code': 'CC BY-NC-ND 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
        'value': 'license_5',
        'src': '88x31(6).png',
        'src_pdf': 'by-nc-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 4.0 International License.'
    },
]
"""Define of list license will be used."""

WEKO_RECORDS_UI_PDF_HEADER_IMAGE_DIR = '/data/pdfcoverpage/'
"""Directory of Image Header of PDF."""

WEKO_RECORDS_UI_EMAIL_ITEM_KEYS = ['creatorMails', 'contributorMails', 'mails']
"""Sub-item keys of Email."""

RECORDS_UI_TOMBSTONE_TEMPLATE = 'weko_records_ui/tombstone.html'
# Setting the template of showing deleted record
