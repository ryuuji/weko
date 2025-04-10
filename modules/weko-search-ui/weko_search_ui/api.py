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

"""WEKO3 module docstring."""


from flask import current_app, json
from invenio_db import db
from weko_admin import config as ad_config
from weko_admin.models import SearchManagement as sm
from weko_index_tree.api import Indexes
from weko_records.utils import get_keywords_data_load


class SearchSetting(object):
    """About search setting."""

    @classmethod
    def get_results_setting(cls):
        """Get result setting."""
        res = sm.get()
        options = dict()
        sort_options = dict()
        display_number = 20
        if res:
            display_number = res.default_dis_num
            res = res.sort_setting.get('allow')
        else:
            return current_app.config['RECORDS_REST_SORT_OPTIONS'], display_number

        for x in res:
            if isinstance(x, dict):
                key_str = x.get('id')
                key = key_str[0:key_str.rfind('_', 1)]
                val = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(
                    current_app.config['SEARCH_UI_SEARCH_INDEX']).get(key)
                if key not in options.keys():
                    options[key] = val

        sort_options[current_app.config['SEARCH_UI_SEARCH_INDEX']] = options

        return sort_options, display_number

    @classmethod
    def get_default_sort(cls, search_type, root_flag=False):
        """Get default sort."""
        res = sm.get()
        sort_str = None
        if res:
            if search_type == current_app.config['WEKO_SEARCH_TYPE_KEYWORD']:
                sort_str = res.default_dis_sort_keyword
            else:
                sort_str = res.default_dis_sort_index
        else:
            if search_type == current_app.config['WEKO_SEARCH_TYPE_KEYWORD']:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS['dlt_keyword_sort_selected']
            else:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS['dlt_index_sort_selected']

        sort_key = sort_str[0:sort_str.rfind('_', 1)]
        sort = sort_str[sort_str.rfind('_', 1) + 1:]

        if root_flag and 'custom_sort' in sort_key:
            if search_type == current_app.config['WEKO_SEARCH_TYPE_KEYWORD']:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS['dlt_keyword_sort_selected']
            else:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS['dlt_index_sort_selected']
            sort_key = sort_str[0:sort_str.rfind('_', 1)]
            sort = sort_str[sort_str.rfind('_', 1) + 1:]

        return sort_key, sort

    @classmethod
    def get_sort_key(cls, key_str):
        """Get sort key."""
        sort_key = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(
            current_app.config['SEARCH_UI_SEARCH_INDEX'], {}).get(
            key_str, {}).get('fields')
        if isinstance(sort_key, list) and len(sort_key) > 0:
            return sort_key[0]
        return None

    @classmethod
    def get_custom_sort(cls, index_id, sort_type):
        """Get custom sort."""
        if sort_type == "asc":
            factor_obj = Indexes.get_item_sort(index_id)
            script_str = {
                "_script": {
                    "script": {
                        "source": "if(params.factor.get(doc[\"control_number\"].value.toString())!=null){params.factor.get(doc[\"control_number\"].value.toString())}else{Integer.MAX_VALUE}",
                        "lang": "painless",
                        "params": {
                            "factor": factor_obj
                        }
                    },
                    "type": "number",
                    "order": "asc"
                }
            }
            default_sort = {'_created': {'order': 'desc',
                                         'unmapped_type': 'long'}}
        else:
            factor_obj = Indexes.get_item_sort(index_id)
            script_str = {
                "_script": {
                    "script": {
                        "source": "if(params.factor.get(doc[\"control_number\"].value.toString())!=null){params.factor.get(doc[\"control_number\"].value.toString())}else{0}",
                        "lang": "painless",
                        "params": {
                            "factor": factor_obj
                        }
                    },
                    "type": "number",
                    "order": "desc"
                }
            }
            default_sort = {'_created': {'order': 'asc',
                                         'unmapped_type': 'long'}}

        return script_str, default_sort

    @classmethod
    def get_nested_sorting(cls, key_str):
        """Get nested sorting object."""
        nested_sorting = None
        sort_option = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(
            current_app.config['SEARCH_UI_SEARCH_INDEX']).get(key_str)
        if sort_option:
            nested_sorting = sort_option.get('nested')
        return nested_sorting


def get_search_detail_keyword(str):
    """Get search detail keyword."""
    res = sm.get()
    options = None
    key_options = dict()
    if res:
        options = res.search_conditions
    else:
        options = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS['detail_condition']

    item_type_list = get_keywords_data_load('')
    check_val = []
    for x in item_type_list:
        sub = dict(id=x[0], contents=x[0], checkStus=False)
        check_val.append(sub)

    for k_v in options:
        if k_v.get('id') == 'itemtype':
            k_v['check_val'] = check_val
            break

    key_options['condition_setting'] = options

    key_options_str = json.dumps(key_options)
    key_options_str.replace('False', 'false')
    key_options_str.replace('True', 'true')

    return key_options_str
