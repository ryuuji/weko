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

"""Item API."""
import re
from collections import OrderedDict

import pytz
from flask import current_app
from flask_security import current_user
from invenio_i18n.ext import current_i18n
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.ext import pid_exists
from invenio_pidstore.models import PersistentIdentifier
from weko_admin.models import AdminSettings
from weko_schema_ui.schema import SchemaTree

from .api import ItemTypes, Mapping


def json_loader(data, pid):
    """Convert the item data and mapping to jpcoar.

    :param data: json from item form post.
    :param pid: pid value.
    :return: dc, jrc, is_edit
    """
    dc = OrderedDict()
    jpcoar = OrderedDict()
    item = dict()
    ar = []
    pubdate = None

    if not isinstance(data, dict) or data.get("$schema") is None:
        return

    item_id = pid.object_uuid
    pid = pid.pid_value

    # get item type id
    index = data["$schema"].rfind('/')
    item_type_id = data["$schema"][index + 1:]

    # get item type mappings
    ojson = ItemTypes.get_record(item_type_id)
    mjson = Mapping.get_record(item_type_id)

    if not (ojson and mjson):
        raise RuntimeError('Item Type {} does not exist.'.format(item_type_id))

    mp = mjson.dumps()
    data.get("$schema")
    for k, v in data.items():
        if k != "pubdate":
            if k == "$schema" or mp.get(k) is None:
                continue

        item.clear()
        try:
            item["attribute_name"] = ojson["properties"][k]["title"] \
                if ojson["properties"][k].get("title") is not None else k
        except Exception:
            pub_date_setting = {
                "type": "string",
                "title": "Publish Date",
                "format": "datetime"
            }
            ojson["properties"]["pubdate"] = pub_date_setting
            item["attribute_name"] = 'Publish Date'
        # set a identifier to add a link on detail page when is a creator field
        # creator = mp.get(k, {}).get('jpcoar_mapping', {})
        # creator = creator.get('creator') if isinstance(
        #     creator, dict) else None
        iscreator = False
        creator = ojson["properties"][k]
        if 'object' == creator["type"]:
            creator = creator["properties"]
            if 'iscreator' in creator:
                iscreator = True
        elif 'array' == creator["type"]:
            creator = creator['items']["properties"]
            if 'iscreator' in creator:
                iscreator = True
        if iscreator:
            item["attribute_type"] = 'creator'

        item_data = ojson["properties"][k]
        if 'array' == item_data.get('type'):
            properties_data = item_data['items']['properties']
            if 'filename' in properties_data:
                item["attribute_type"] = 'file'

        if isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], dict):
                item["attribute_value_mlt"] = v
            else:
                item["attribute_value"] = v
        elif isinstance(v, dict):
            ar.append(v)
            item["attribute_value_mlt"] = ar
            ar = []
        else:
            item["attribute_value"] = v

        dc[k] = item.copy()
        if k != "pubdate":
            item.update(mp.get(k))
        else:
            pubdate = v
        jpcoar[k] = item.copy()

    # convert to es jpcoar mapping data
    jrc = SchemaTree.get_jpcoar_json(jpcoar)
    list_key = []
    for k, v in jrc.items():
        if not v:
            list_key.append(k)
    if list_key:
        for key in list_key:
            del jrc[key]
    if dc:
        # get the tile name to detail page
        title = data.get("title")

        if 'control_number' in dc:
            del dc['control_number']

        dc.update(dict(item_title=title))
        dc.update(dict(item_type_id=item_type_id))
        dc.update(dict(control_number=pid))

        # check oai id value
        is_edit = False
        try:
            oai_value = PersistentIdentifier.get_by_object(
                pid_type='oai',
                object_type='rec',
                object_uuid=PersistentIdentifier.get('recid', pid).object_uuid
            ).pid_value
            is_edit = pid_exists(oai_value, 'oai')
        except PIDDoesNotExistError:
            pass

        if not is_edit:
            oaid = current_pidstore.minters['oaiid'](item_id, dc)
            oai_value = oaid.pid_value
        # relation_ar = []
        # relation_ar.append(dict(value="", item_links="", item_title=""))
        # jrc.update(dict(relation=dict(relationType=relation_ar)))
        # dc.update(dict(relation=dict(relationType=relation_ar)))
        jrc.update(dict(control_number=pid))
        jrc.update(dict(_oai={"id": oai_value}))
        jrc.update(dict(_item_metadata=dc))
        jrc.update(dict(itemtype=ojson.model.item_type_name.name))
        jrc.update(dict(publish_date=pubdate))

        # save items's creator to check permission
        if current_user:
            current_user_id = current_user.get_id()
        else:
            current_user_id = '1'
        if current_user_id:
            # jrc is saved on elastic
            jrc_weko_shared_id = jrc.get("weko_shared_id", None)
            jrc_weko_creator_id = jrc.get("weko_creator_id", None)
            if not jrc_weko_creator_id:
                # in case first time create record
                jrc.update(dict(weko_creator_id=current_user_id))
                jrc.update(dict(weko_shared_id=data.get('shared_user_id',
                                                        None)))
            else:
                # incase record is end and someone is updating record
                if current_user_id == int(jrc_weko_creator_id):
                    # just allow owner update shared_user_id
                    jrc.update(dict(weko_shared_id=data.get('shared_user_id',
                                                            None)))

            # dc js saved on postgresql
            dc_owner = dc.get("owner", None)
            if not dc_owner:
                dc.update(
                    dict(
                        weko_shared_id=data.get(
                            'shared_user_id',
                            None)))
                dc.update(dict(owner=current_user_id))
            else:
                if current_user_id == int(dc_owner):
                    dc.update(dict(weko_shared_id=data.get('shared_user_id',
                                                           None)))

    del ojson, mjson, item
    return dc, jrc, is_edit


def set_timestamp(jrc, created, updated):
    """Set timestamp."""
    jrc.update(
        {"_created": pytz.utc.localize(created)
            .isoformat() if created else None})

    jrc.update(
        {"_updated": pytz.utc.localize(updated)
            .isoformat() if updated else None})


def sort_records(records, form):
    """Sort records.

    :param records:
    :param form:
    :return:
    """
    odd = OrderedDict()
    if isinstance(records, dict) and isinstance(form, list):
        for k in find_items(form):
            val = records.get(k[0])
            if val:
                odd.update({k[0]: val})
        # save schema link
        odd.update({"$schema": records.get("$schema")})
        del records
        return odd
    else:
        return records


def sort_op(record, kd, form):
    """Sort options dict.

    :param record:
    :param kd:
    :param form:
    :return:
    """
    odd = OrderedDict()
    if isinstance(record, dict) and isinstance(form, list):
        index = 0
        for k in find_items(form):
            # mapping target key
            key = kd.get(k[0])
            if not odd.get(key) and record.get(key):
                index += 1
                val = record.pop(key, {})
                val['index'] = index
                odd.update({key: val})

        record.clear()
        del record
        return odd
    else:
        return record


def find_items(form):
    """Find sorted items into a list.

    :param form:
    :return: lst
    """
    lst = []

    def find_key(node):
        if isinstance(node, dict):
            key = node.get('key')
            title = node.get('title', '')
            try:
                # Try catch for case this function is called from celery app
                current_lang = current_i18n.language
            except Exception:
                current_lang = 'en'
            title_i18n = node.get('title_i18n', {})\
                .get(current_lang, title)
            option = {
                'required': node.get('required', False),
                'show_list': node.get('isShowList', False),
                'specify_newline': node.get('isSpecifyNewline', False),
                'hide': node.get('isHide', False),
            }
            val = ''
            if key:
                yield [key, title, title_i18n, option, val]
            for v in node.values():
                if isinstance(v, list):
                    for k in find_key(v):
                        yield k
        elif isinstance(node, list):
            for n in node:
                for k in find_key(n):
                    yield k

    for x in find_key(form):
        lst.append(x)

    return lst


def get_all_items(nlst, klst, is_get_name=False):
    """Convert and sort item list.

    :param nlst:
    :param klst:
    :param is_get_name:
    :return: alst
    """
    def get_name(key):
        for lst in klst:
            key_arr = lst[0].split('.')
            k = key_arr[-1]
            if key != k:
                continue
            item_name = lst[1]
            if len(key_arr) >= 3:
                parent_key = key_arr[-2].replace('[]', '')
                parent_key_name = get_name(parent_key)
                if item_name and parent_key_name:
                    item_name = item_name + '.' + get_name(parent_key)

            return item_name

    def get_items(nlst):
        _list = []

        if isinstance(nlst, list):
            for lst in nlst:
                _list.append(get_items(lst))
        if isinstance(nlst, dict):
            d = {}
            for k, v in nlst.items():
                if isinstance(v, str):
                    d[k] = v
                    if is_get_name:
                        item_name = get_name(k)
                        if item_name:
                            d[k + '.name'] = item_name
                else:
                    _list.append(get_items(v))
            _list.append(d)

        return _list

    to_orderdict(nlst, klst)
    alst = get_items(nlst)

    return alst


def get_all_items2(nlst, klst):
    """Convert and sort item list(original).

    :param nlst:
    :param klst:
    :return: alst
    """
    alst = []

    # def get_name(key):
    #     for lst in klst:
    #         k = lst[0].split('.')[-1]
    #         if key == k:
    #             return lst[1]
    def get_items(nlst):
        if isinstance(nlst, dict):
            for k, v in nlst.items():
                if isinstance(v, str):
                    alst.append({k: v})
                else:
                    get_items(v)
        elif isinstance(nlst, list):
            for lst in nlst:
                get_items(lst)

    to_orderdict(nlst, klst)
    get_items(nlst)
    return alst


def to_orderdict(alst, klst):
    """Sort item list.

    :param alst:
    :param klst:
    """
    if isinstance(alst, list):
        for i in range(len(alst)):
            if isinstance(alst[i], dict):
                alst.insert(i, OrderedDict(alst.pop(i)))
                to_orderdict(alst[i], klst)
    elif isinstance(alst, dict):
        nlst = []
        if isinstance(klst, list):
            for lst in klst:
                key = lst[0].split('.')[-1]
                val = alst.pop(key, {})
                if val:
                    if isinstance(val, dict):
                        val = OrderedDict(val)
                    nlst.append({lst[0]: val})
                if not alst:
                    break

            while len(nlst) > 0:
                alst.update(nlst.pop(0))

            for k, v in alst.items():
                if not isinstance(v, str):
                    to_orderdict(v, klst)


def get_options_and_order_list(item_type_id):
    """Get Options by item type id.

    :param item_type_id:
    :return: options dict and sorted list
    """
    ojson = ItemTypes.get_record(item_type_id)
    solst = find_items(ojson.model.form)
    meta_options = ojson.model.render.get('meta_fix')
    meta_options.update(ojson.model.render.get('meta_list'))
    return solst, meta_options


def sort_meta_data_by_options(record_hit):
    """Reset metadata by '_options'.

    :param record_hit:
    """
    from weko_records_ui.permissions import check_file_download_permission

    def get_meta_values(v):
        """Get values from metadata."""
        data_list = []

        def get_values(v):
            """Get value by recursive."""
            if isinstance(v, list):
                for temp in v:
                    get_values(temp)
            elif isinstance(v, dict):
                for temp in v.values():
                    data_list.append(temp)
            elif isinstance(v, str):
                data_list.append(v)

        get_values(v)
        return data_list

    def convert_data_to_dict(solst):
        """Convert solst to dict."""
        solst_dict_array = []
        for lst in solst:
            key = lst[0]
            option = meta_options.get(key, {}).get('option')
            temp = {
                'key': key,
                'title': lst[1],
                'title_ja': lst[2],
                'option': lst[3],
                'parent_option': option,
                'value': ''
            }
            solst_dict_array.append(temp)
        return solst_dict_array

    def get_comment(solst_dict_array, hide_email_flag):
        """Check and get info."""
        result = []
        _ignore_items = list()
        _license_dict = current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
        if _license_dict:
            _ignore_items.append(_license_dict[0].get('value'))

        for s in solst_dict_array:
            value = s['value']
            option = s['option']
            if value and value not in _ignore_items:
                parent_option = s['parent_option']
                is_show_list = parent_option.get(
                    'show_list') if parent_option.get(
                    'show_list') else option.get('show_list')
                is_specify_newline = parent_option.get(
                    'specify_newline') if parent_option.get(
                    'specify_newline') else option.get('specify_newline')
                is_hide = parent_option.get('hide') if parent_option.get(
                    'hide') else option.get('hide')
                if 'creatorMails[].creatorMail' in s['key'] \
                        or 'contributorMails[].contributorMail' in s['key'] \
                        or 'mails[].mail' in s['key']:
                    is_hide = is_hide | hide_email_flag
                if not is_hide and is_show_list:
                    if is_specify_newline or len(result) == 0:
                        result.append(value)
                    else:
                        result[-1] += "," + value
        return result

    def get_file_comments(record, files):
        """Check and get file info."""
        result = []
        for f in files:
            if check_file_download_permission(record, f, False):
                extention = ''
                label = f.get('url', {}).get('label')
                filename = f.get('filename', '')
                if not label and not f.get('version_id'):
                    label = f.get('url', {}).get('url', '')
                elif not label:
                    label = filename

                if f.get('version_id'):
                    idx = filename.find('.') + 1
                    extention = filename[idx:] if idx > 0 else 'unknown'

                if label:
                    result.append({
                        'label': label,
                        'extention': extention,
                        'url': f.get('url', {}).get('url', '')
                    })
        return result

    def get_file_thumbnail(thumbnails):
        """Get file thumbnail."""
        thumbnail = {}
        if thumbnails and len(thumbnails) > 0:
            subitem_thumbnails = thumbnails[0].get('subitem_thumbnail')
            if subitem_thumbnails and len(subitem_thumbnails) > 0:
                thumbnail = {
                    'thumbnail_label': subitem_thumbnails[0].get('thumbnail_label', ''),
                    'thumbnail_width': current_app.config['WEKO_RECORDS_UI_DEFAULT_MAX_WIDTH_THUMBNAIL']
                }
        return thumbnail

    try:
        src = record_hit['_source'].pop('_item_metadata')
        item_type_id = record_hit['_source'].get('item_type_id') \
            or src.get('item_type_id')
        if not item_type_id:
            return
        solst, meta_options = get_options_and_order_list(item_type_id)
        solst_dict_array = convert_data_to_dict(solst)
        files_info = []
        thumbnail = None
        # Set value and parent option
        for lst in solst:
            key = lst[0]
            val = src.get(key)
            option = meta_options.get(key, {}).get('option')
            if not val or not option:
                continue
            mlt = val.get('attribute_value_mlt', [])
            if mlt:
                if val.get('attribute_type', '') == 'file' \
                        and not option.get("hidden") \
                        and option.get("showlist"):
                    files_info = get_file_comments(src, mlt)
                    continue
                is_thumbnail = any('subitem_thumbnail' in data for data in mlt)
                if is_thumbnail and not option.get("hidden") \
                        and option.get("showlist"):
                    thumbnail = get_file_thumbnail(mlt)
                    continue
                meta_data = get_all_items2(mlt, solst)
                for m in meta_data:
                    for s in solst_dict_array:
                        s_key = s.get('key')
                        if m.get(s_key):
                            s['value'] = m.get(s_key) if not s['value'] else \
                                '{}, {}'.format(s['value'], m.get(s_key))
                            s['parent_option'] = {
                                'required': option.get("required"),
                                'show_list': option.get("showlist"),
                                'specify_newline': option.get("crtf"),
                                'hide': option.get("hidden")
                            }
                            break
        settings = AdminSettings.get('items_display_settings')
        items = get_comment(solst_dict_array, not settings.items_display_email)
        if items:
            if record_hit['_source'].get('_comment'):
                record_hit['_source']['_comment'].extend(items)
            else:
                record_hit['_source']['_comment'] = items
        if files_info:
            record_hit['_source']['_files_info'] = files_info
        if thumbnail:
            record_hit['_source']['_thumbnail'] = thumbnail
    except Exception:
        current_app.logger.exception(
            u'Record serialization failed {}.'.format(
                str(record_hit['_source'].get('control_number'))))
    return


def get_keywords_data_load(str):
    """Get a json of item type info.

    :return: dict of item type info
    """
    try:
        return [(x.name, x.id) for x in ItemTypes.get_latest()]
    except BaseException:
        pass
    return []


def is_valid_openaire_type(resource_type, communities):
    """Check if the OpenAIRE subtype is corresponding with other metadata.

    :param resource_type: Dictionary corresponding to 'resource_type'.
    :param communities: list of communities identifiers
    :returns: True if the 'openaire_subtype' (if it exists) is valid w.r.t.
        the `resource_type.type` and the selected communities, False otherwise.
    """
    if 'openaire_subtype' not in resource_type:
        return True
    oa_subtype = resource_type['openaire_subtype']
    prefix = oa_subtype.split(':')[0] if ':' in oa_subtype else ''

    cfg = current_openaire.openaire_communities
    defined_comms = [c for c in cfg.get(prefix, {}).get('communities', [])]
    type_ = resource_type['type']
    subtypes = cfg.get(prefix, {}).get('types', {}).get(type_, [])
    # Check if the OA subtype is defined in config and at least one of its
    # corresponding communities is present
    is_defined = any(t['id'] == oa_subtype for t in subtypes)
    comms_match = len(set(communities) & set(defined_comms))
    return is_defined and comms_match


def check_has_attribute_value(node):
    """Check has value in items.

    :param node:
    :return: boolean
    """
    try:
        if isinstance(node, list):
            for lst in node:
                return check_has_attribute_value(lst)
        elif isinstance(node, dict) and bool(node):
            for val in node.values():
                if val:
                    if isinstance(val, str):
                        return True
                    else:
                        return check_has_attribute_value(val)
        return False
    except BaseException as e:
        current_app.logger.error(
            'Function check_has_attribute_value error:', e)
        return False


def get_attribute_value_all_items(
        root_key,
        nlst,
        klst,
        is_author=False,
        hide_email_flag=True):
    """Convert and sort item list.

    :param root_key:
    :param nlst:
    :param klst:
    :param is_author:
    :return: alst
    """
    def get_name(key):
        for lst in klst:
            keys = lst[0].replace("[]", "").split('.')
            if keys[0].startswith(root_key) and key == keys[-1]:
                return lst[2] if not is_author else '{}.{}'. format(
                    key, lst[2])

    def to_sort_dict(alst, klst):
        """Sort item list.

        :param alst:
        :param klst:
        """
        if isinstance(klst, list):
            result = []
            try:
                if isinstance(alst, list):
                    for a in alst:
                        result.append(to_sort_dict(a, klst))
                else:
                    temp = []
                    for lst in klst:
                        key = lst[0].split('.')[-1]
                        val = alst.pop(key, {})
                        hide = lst[3].get('hide')
                        if key in ('creatorMail', 'contributorMail', 'mail'):
                            hide = hide | hide_email_flag
                        if val and (isinstance(val, str)
                                    or (key == 'nameIdentifier')):
                            if not hide:
                                temp.append({key: val})
                        elif isinstance(val, list) and len(
                                val) > 0 and isinstance(val[0], str):
                            if not hide:
                                temp.append({key: val})
                        else:
                            if check_has_attribute_value(val):
                                if not hide:
                                    res = to_sort_dict(val, klst)
                                    temp.append({key: res})
                        if not alst:
                            break
                    result.append(temp)
                return result
            except BaseException as e:
                current_app.logger.error('Function to_sort_dict error: ', e)
                return result

    def set_attribute_value(nlst):
        _list = []
        try:
            if isinstance(nlst, list):
                for lst in nlst:
                    _list.append(set_attribute_value(lst))
            # check OrderedDict is dict and not empty
            elif isinstance(nlst, dict) and bool(nlst):
                d = {}
                for key, val in nlst.items():
                    item_name = get_name(key) or ''
                    if val and (isinstance(val, str)
                                or (key == 'nameIdentifier')):
                        # the last children level
                        d[item_name] = val
                    elif isinstance(val, list) and len(val) > 0 and isinstance(
                            val[0], str):
                        d[item_name] = ', '.join(val)
                    else:
                        # parents level
                        # check if have any child
                        if check_has_attribute_value(val):
                            d[item_name] = set_attribute_value(val)
                _list.append(d)
            return _list
        except BaseException as e:
            current_app.logger.error('Function set_node error: ', e)
            return _list

    orderdict = to_sort_dict(nlst, klst)
    alst = set_attribute_value(orderdict)

    return alst


def check_input_value(old, new):
    """Check different between old and new data.

    @param old:
    @param new:
    @return:
    """
    diff = False
    for k in old.keys():
        if old[k]['input_value'] != new[k]['input_value']:
            diff = True
            break
    return diff


def remove_key(removed_key, item_val):
    """Remove removed_key out of item_val.

    @param removed_key:
    @param item_val:
    @return:
    """
    if not isinstance(item_val, dict):
        return
    if removed_key in item_val.keys():
        del item_val[removed_key]
    for k, v in item_val.items():
        remove_key(removed_key, v)


def remove_keys(excluded_keys, item_val):
    """Remove removed_key out of item_val.

    @param removed_key:
    @param item_val:
    @return:
    """
    if not isinstance(item_val, dict):
        return
    key_list = item_val.keys()
    for excluded_key in excluded_keys:
        if excluded_key in key_list:
            del item_val[excluded_key]
    for k, v in item_val.items():
        remove_keys(excluded_keys, v)


def remove_multiple(schema):
    """Remove multiple of schema.

    @param schema:
    @return:
    """
    for k in schema['properties'].keys():
        if 'maxItems' and 'minItems' in schema['properties'][k].keys():
            del schema['properties'][k]['maxItems']
            del schema['properties'][k]['minItems']
        if 'items' in schema['properties'][k].keys():
            schema['properties'][k] = schema['properties'][k]['items']


def check_to_upgrade_version(old_render, new_render):
    """Check upgrade or keep version by checking different renders data.

    @param old_render:
    @param new_render:
    @return:
    """
    if old_render.get('meta_list').keys() != \
            new_render.get('meta_list').keys():
        return True
    # Check diff input value:
    if check_input_value(old_render.get('meta_list'),
                         new_render.get('meta_list')):
        return True
    # Check diff schema
    old_schema = old_render.get('table_row_map').get('schema')
    new_schema = new_render.get('table_row_map').get('schema')

    excluded_keys = \
        current_app.config['WEKO_ITEMTYPE_EXCLUDED_KEYS']
    remove_keys(excluded_keys, old_schema)
    remove_keys(excluded_keys, new_schema)

    remove_multiple(old_schema)
    remove_multiple(new_schema)
    if old_schema != new_schema:
        return True
    return False


def remove_weko2_special_character(s: str):
    """Remove special character of WEKO2.

    :param s:
    """
    def __remove_special_character(_s_str: str):
        pattern = r"(^(&EMPTY&,|,&EMPTY&)|(&EMPTY&,|,&EMPTY&)$|&EMPTY&)"
        _s_str = re.sub(pattern, '', _s_str)
        if _s_str == ',':
            return ''
        return _s_str.strip() if _s_str != ',' else ''

    s = s.strip()
    esc_str = ""
    for i in s:
        if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
            esc_str += i
    esc_str = __remove_special_character(esc_str)
    return esc_str
