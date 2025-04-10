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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module of weko-items-autofill utils.."""
from functools import wraps

from flask import current_app
from invenio_cache import current_cache
from invenio_db import db
from lxml import etree
from weko_records.api import ItemTypes, Mapping
from weko_workflow.models import ActionJournal

from . import config
from .api import CiNiiURL, CrossRefOpenURL


def is_update_cache():
    """Return True if Autofill Api has been updated."""
    return current_app.config['WEKO_ITEMS_AUTOFILL_API_UPDATED']


def cached_api_json(timeout=50, key_prefix="cached_api_json"):
    """Cache Api response data.

    :param timeout: Cache timeout
    :param key_prefix: prefix key
    :return:
    """
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = key_prefix
            for value in args:
                key += str(value)
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=key,
                forced_update=is_update_cache,
            )
            if current_cache.get(key) is None:
                data = cache_fun(f)(*args, **kwargs)
                current_cache.set(key, data)
                return data
            else:
                return current_cache.get(key)

        return wrapper

    return caching


def get_item_id(item_type_id):
    """Get dictionary contain item id.

    Get from mapping between item type and jpcoar
    :param item_type_id: The item type id
    :return: dictionary
    """
    def _get_jpcoar_mapping(rtn_results, jpcoar_data):
        for u, s in jpcoar_data.items():
            if rtn_results.get(u) is not None:
                data = list()
                if isinstance(rtn_results.get(u), list):
                    data = rtn_results.get(u)
                    data.append({u: {**s, "model_id": k}})
                else:
                    rtn_results.get(u)
                    data.append({u: rtn_results.get(u)})
                    data.append({u: {**s, "model_id": k}})
                rtn_results[u] = data
            else:
                rtn_results[u] = s
                rtn_results[u]['model_id'] = k

    results = dict()
    item_type_mapping = Mapping.get_record(item_type_id)
    try:
        for k, v in item_type_mapping.items():
            jpcoar = v.get("jpcoar_mapping")
            if isinstance(jpcoar, dict):
                _get_jpcoar_mapping(results, jpcoar)
    except Exception as e:
        current_app.logger.debug(e)
        results['error'] = str(e)

    return results


def convert_html_escape(text):
    """Convert escape HTML to character.

    :type text: String
    """
    if not isinstance(text, str):
        return
    html_escape = {
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
        "&gt;": ">",
        "&lt;": "<",
    }
    try:
        for key, value in html_escape.items():
            text = text.replace(key, value)
    except Exception as e:
        current_app.logger.debug(e)

    return text


def _get_title_data(jpcoar_data, key, rtn_title):
    """Get title data.

    @param jpcoar_data: JPCOAR data
    @param key: index key
    @param rtn_title: title list
    """
    try:
        if str(key).index('item') is not None:
            rtn_title['title_parent_key'] = key
            title_value = jpcoar_data['title']
            if '@value' in title_value.keys():
                rtn_title['title_value_lst_key'] = title_value[
                    '@value'].split('.')
            if '@attributes' in title_value.keys():
                title_lang = title_value['@attributes']
                if 'xml:lang' in title_lang.keys():
                    rtn_title['title_lang_lst_key'] = title_lang[
                        'xml:lang'].split('.')
    except Exception as e:
        current_app.logger.debug(e)


def get_title_pubdate_path(item_type_id):
    """Get title and pubdate path.

    :param item_type_id:
    :return: result json.
    """
    result = {
        'title': '',
        'pubDate': ''
    }
    item_type_mapping = Mapping.get_record(item_type_id)
    title = dict()
    for k, v in sorted(item_type_mapping.items()):
        jpcoar = v.get("jpcoar_mapping")
        if isinstance(jpcoar, dict) and 'title' in jpcoar.keys():
            _get_title_data(jpcoar, k, title)
            if title:
                break
    result['title'] = title
    return result


@cached_api_json(timeout=50, key_prefix="crossref_data")
def get_crossref_record_data(pid, doi, item_type_id):
    """Get record data base on CrossRef API.

    :param pid: The PID
    :param doi: The DOI ID
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = CrossRefOpenURL(pid, doi).get_data()
    if api_response["error"]:
        return result
    api_response['response'] = convert_crossref_xml_data_to_dictionary(
        api_response['response'])
    api_data = get_crossref_data_by_key(api_response, 'all')
    with db.session.no_autoflush:
        items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_crossref_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data)
    return result


@cached_api_json(timeout=50, key_prefix="cinii_data")
def get_cinii_record_data(naid, item_type_id):
    """Get record data base on CiNii API.

    :param naid: The CiNii ID
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = CiNiiURL(naid).get_data()
    if api_response["error"] \
            or not isinstance(api_response['response'], dict):
        return result
    api_data = get_cinii_data_by_key(api_response, 'all')
    items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_cinii_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data)
    return result


def get_basic_cinii_data(data):
    """Get basic data template from CiNii.

        Basic value format:
        {
            '@value': value,
            '@language': language
        }

    :param: data: CiNii data
    :return: list converted data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        new_data = dict()
        new_data['@value'] = item.get('@value')
        if item.get('@language'):
            new_data['@language'] = item.get('@language')
        else:
            new_data['@language'] = default_language
        result.append(new_data)
    return result


def pack_single_value_as_dict(data):
    """Pack value as dictionary.

    Based on return format
    {
        '@value': value
    }

    :param: data: data need to pack
    :return: dictionary contain packed data
    """
    new_data = dict()
    new_data['@value'] = data
    return new_data


def pack_data_with_multiple_type_cinii(data1, type1, data2, type2):
    """Map CiNii multi data with type.

    Arguments:
        data1
        type1
        data2
        type2

    Returns:
        packed data

    """
    result = list()
    if data1:
        new_data = dict()
        new_data['@value'] = data1
        new_data['@type'] = type1
        result.append(new_data)
    if data2:
        new_data = dict()
        new_data['@value'] = data2
        new_data['@type'] = type2
        result.append(new_data)
    return result


def get_cinii_creator_data(data):
    """Get creator data from CiNii.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: creator data
    :return: list of creator name
    """
    result = list()
    default_language = 'ja'
    for item in data:
        for i in range(0, len(item)):
            new_data = dict()
            new_data['@value'] = item[i].get('@value')
            if item[i].get('@language'):
                new_data['@language'] = item[i].get('@language')
            else:
                new_data['@language'] = default_language
            result.append(new_data)
    return result


def get_cinii_contributor_data(data):
    """Get contributor data from CiNii.

    Get contributor name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        if item.get('con:organization') is None:
            continue
        organization = item['con:organization'][0]
        if organization.get('foaf:name') is None:
            continue
        for i in range(0, len(organization.get('foaf:name'))):
            new_data = dict()
            new_data['@value'] = organization['foaf:name'][i].get('@value')
            if organization['foaf:name'][i].get('@language'):
                language = organization['foaf:name'][i].get('@language')
                new_data['@language'] = language
            else:
                new_data['@language'] = default_language
            result.append(new_data)
    return result


def get_cinii_description_data(data):
    """Get description data from CiNii.

    Get description and form it as format:
    {
        '@value': description,
        '@language': language,
        '@type': type of description
    }

    :param: description data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        new_data = dict()
        new_data['@value'] = item.get('@value')
        new_data['@type'] = 'Abstract'
        if item.get('@language'):
            new_data['@language'] = item.get('@language')
        else:
            new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_subject_data(data):
    """Get subject data from CiNii.

    Get subject and form it as format:
    {
        '@value': title,
        '2language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    :param: data: subject data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for sub in data:
        new_data = dict()
        new_data['@scheme'] = 'Other'
        new_data['@URI'] = sub.get('@id')
        title = sub.get('dc:title')
        if title[0] is not None:
            new_data['@value'] = title[0].get('@value')
            if title[0].get('@language'):
                new_data['@language'] = title[0].get('@language')
            else:
                new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_page_data(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except Exception as e:
        current_app.logger.debug(e)
        return pack_single_value_as_dict(None)


def get_cinii_numpage(data):
    """Get number of page.

    If CiNii have pageRange, get number of page
    If not, number of page equals distance between start and end page

    :param: data: CiNii data
    :return: number of page is packed
    """
    if data.get('prism:pageRange'):
        return get_cinii_page_data(data.get('prism:pageRange'))
    else:
        try:
            end = int(data.get('prism:endingPage'))
            start = int(data.get('prism:startingPage'))
            num_pages = end - start + 1
            return pack_single_value_as_dict(str(num_pages))
        except Exception as e:
            current_app.logger.debug(e)
            return pack_single_value_as_dict(None)


def get_cinii_date_data(data):
    """Get publication date.

    Get publication date from CiNii data
    format:
    {
        '@value': date
        '@type': type of date
    }

    :param: data: date
    :return: date and date type is packed
    """
    result = dict()
    if len(data.split('-')) != 3:
        result['@value'] = None
        result['@type'] = None
    else:
        result['@value'] = data
        result['@type'] = 'Issued'
    return result


def get_cinii_data_by_key(api, keyword):
    """Get data from CiNii based on keyword.

    :param: api: CiNii data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    data_response = api['response'].get('@graph')
    result = dict()
    if data_response is None:
        return result
    data = data_response[0]
    if (keyword == 'title' or keyword == 'alternative') \
            and data.get('dc:title'):
        result[keyword] = get_basic_cinii_data(data.get('dc:title'))
    elif keyword == 'creator' and data.get('dc:creator'):
        result[keyword] = get_cinii_creator_data(data.get('dc:creator'))
    elif keyword == 'contributor' and data.get('foaf:maker'):
        result[keyword] = get_cinii_contributor_data(data.get('foaf:maker'))
    elif keyword == 'description' and data.get('dc:description'):
        result[keyword] = get_cinii_description_data(
            data.get('dc:description')
        )
    elif keyword == 'subject' and data.get('foaf:topic'):
        result[keyword] = get_cinii_subject_data(data.get('foaf:topic'))
    elif keyword == 'sourceTitle' and data.get('prism:publicationName'):
        result[keyword] = get_basic_cinii_data(
            data.get('prism:publicationName')
        )
    elif keyword == 'volume' and data.get('prism:volume'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:volume'))
    elif keyword == 'issue' and data.get('prism:number'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:number'))
    elif keyword == 'pageStart' and data.get('prism:startingPage'):
        result[keyword] = get_cinii_page_data(data.get('prism:startingPage'))
    elif keyword == 'pageEnd' and data.get('prism:endingPage'):
        result[keyword] = get_cinii_page_data(data.get('prism:endingPage'))
    elif keyword == 'numPages':
        result[keyword] = get_cinii_numpage(data)
    elif keyword == 'date' and data.get('prism:publicationDate'):
        result[keyword] = get_cinii_date_data(
            data.get('prism:publicationDate'))
    elif keyword == 'publisher' and data.get('dc:publisher'):
        result[keyword] = get_basic_cinii_data(data.get('dc:publisher'))
    elif keyword == 'sourceIdentifier':
        result[keyword] = pack_data_with_multiple_type_cinii(
            data.get('prism:issn'),
            'ISSN',
            data.get('cinii:ncid'),
            'NCID'
        )
    elif keyword == 'relation':
        result[keyword] = pack_data_with_multiple_type_cinii(
            data.get('cinii:naid'),
            'NAID',
            data.get('prism:doi'),
            'DOI'
        )
    elif keyword == 'all':
        for key in current_app.config[
                'WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM']:
            result[key] = get_cinii_data_by_key(api, key).get(key)
    return result


def get_crossref_title_data(data):
    """Get title data from CrossRef.

    Arguments:
        data -- title data

    Returns:
        Packed title data

    """
    result = list()
    default_language = 'en'
    if isinstance(data, list):
        for title in data:
            new_data = dict()
            new_data['@value'] = title
            new_data['@language'] = default_language
            result.append(new_data)
    else:
        new_data = dict()
        new_data['@value'] = data
        new_data['@language'] = default_language
        result.append(new_data)
    return result


def _build_name_data(data):
    """Build name data from CrossRef data.

    @param data: CrossRef data
    @return: Name list
    """
    result = list()
    default_language = 'en'
    for name_data in data:
        family_name = name_data.get('family')
        given_name = name_data.get('given')
        full_name = ''
        if given_name and family_name:
            full_name = family_name + " " + given_name
        elif given_name:
            full_name = given_name
        elif family_name:
            full_name = family_name
        new_data = dict()
        new_data['@value'] = full_name
        new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_crossref_creator_data(data):
    """Get creator name from CrossRef data.

    Arguments:
        data -- CrossRef data

    """
    return _build_name_data(data)


def get_crossref_contributor_data(data):
    """Get contributor name from CrossRef data.

    Arguments:
        data -- CrossRef data

    """
    return _build_name_data(data)


def get_start_and_end_page(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except ValueError as e:
        current_app.logger.debug(e)
        return pack_single_value_as_dict(None)


def get_crossref_issue_date(data):
    """Get CrossRef issued date.

    Arguments:
        data -- issued data

    Returns:
        Issued date is packed

    """
    result = dict()
    if data:
        result['@value'] = data
        result['@type'] = 'Issued'
    else:
        result['@value'] = None
        result['@type'] = None
    return result


def get_crossref_source_title_data(data):
    """Get source title information.

    Arguments:
        data -- created data

    Returns:
        Source title  data

    """
    new_data = dict()
    default_language = 'en'
    new_data['@value'] = data
    new_data['@language'] = default_language
    return new_data


def get_crossref_publisher_data(data):
    """Get publisher information.

    Arguments:
        data -- created data

    Returns:
        Publisher packed data

    """
    new_data = dict()
    default_language = 'en'
    new_data['@value'] = data
    new_data['@language'] = default_language
    return new_data


def get_crossref_relation_data(isbn, doi):
    """Get CrossRef relation data.

    :param isbn, doi:
    :return:
    """
    result = list()
    if doi:
        new_data = dict()
        new_data['@value'] = doi
        new_data['@type'] = "DOI"
        result.append(new_data)
    if isbn and len(result) == 0:
        for element in isbn:
            new_data = dict()
            new_data['@value'] = element
            new_data['@type'] = "ISBN"
            result.append(new_data)
    if len(result) == 0:
        return pack_single_value_as_dict(None)
    return result


def get_crossref_source_data(data):
    """Get CrossRef source data.

    :param data:
    :return:
    """
    result = list()
    if data:
        new_data = dict()
        new_data['@value'] = data
        new_data['@type'] = 'ISSN'
        result.append(new_data)
    return result


def get_crossref_data_by_key(api, keyword):
    """Get CrossRef data based on keyword.

    Arguments:
        api: CrossRef data
        keyword: search keyword

    Returns:
        CrossRef data for keyword

    """
    if api['error'] or api['response'] is None:
        return None

    data = api['response']
    result = dict()
    if keyword == 'title' and data.get('article_title'):
        result[keyword] = get_crossref_title_data(data.get('article_title'))
    elif keyword == 'creator' and data.get('author'):
        result[keyword] = get_crossref_creator_data(data.get('author'))
    elif keyword == 'contributor' and data.get('contributor'):
        result[keyword] = get_crossref_contributor_data(data.get('contributor'))
    elif keyword == 'sourceTitle' and data.get('journal_title'):
        result[keyword] = get_crossref_source_title_data(
            data.get('journal_title')
        )
    elif keyword == 'volume' and data.get('volume'):
        result[keyword] = pack_single_value_as_dict(data.get('volume'))
    elif keyword == 'issue' and data.get('issue'):
        result[keyword] = pack_single_value_as_dict(data.get('issue'))
    elif keyword == 'pageStart' and data.get('first_page'):
        result[keyword] = get_start_and_end_page(data.get('first_page'))
    elif keyword == 'pageEnd' and data.get('last_page'):
        result[keyword] = get_start_and_end_page(data.get('last_page'))
    elif keyword == 'date' and data.get('year'):
        result[keyword] = get_crossref_issue_date(data.get('year'))
    elif keyword == 'relation':
        result[keyword] = get_crossref_relation_data(
            data.get('isbn'),
            data.get('doi')
        )
    elif keyword == 'sourceIdentifier':
        result[keyword] = get_crossref_source_data(data.get('issn'))
    elif keyword == 'all':
        for key in current_app.config[
                'WEKO_ITEMS_AUTOFILL_CROSSREF_REQUIRED_ITEM']:
            result[key] = get_crossref_data_by_key(api, key).get(key)
    return result


def get_cinii_autofill_item(item_id):
    """Get CiNii autofill item.

    :param item_id: Item ID.
    :return:
    """
    jpcoar_item = get_item_id(item_id)
    cinii_req_item = dict()
    for key in current_app.config['WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM']:
        if jpcoar_item.get(key) is not None:
            cinii_req_item[key] = jpcoar_item.get(key)
    return cinii_req_item


def get_crossref_autofill_item(item_id):
    """Get CrossRef autofill item.

    :param item_id: Item ID
    :return:
    """
    jpcoar_item = get_item_id(item_id)
    crossref_req_item = dict()
    for key in current_app.config[
            'WEKO_ITEMS_AUTOFILL_CROSSREF_REQUIRED_ITEM']:
        if jpcoar_item.get(key) is not None:
            crossref_req_item[key] = jpcoar_item.get(key)
    return crossref_req_item


def get_autofill_key_tree(schema_form, item, result=None):
    """Get auto fill key tree.

    :param schema_form: schema form
    :param item: The mapping items
    :param result: The key result
    :return: Autofill key tree
    """
    if result is None:
        result = dict()
    if not isinstance(item, dict):
        return None

    for key, val in item.items():
        if isinstance(val, dict) and 'model_id' in val.keys():
            parent_key = val['model_id']
            key_data = dict()
            if parent_key == "pubdate":
                continue
            if key == "creator":
                creator_name_object = val.get("creatorName")
                if creator_name_object:
                    key_data = get_key_value(schema_form,
                                             creator_name_object, parent_key)
            elif key == "contributor":
                contributor_name = val.get("contributorName")
                if contributor_name:
                    key_data = get_key_value(schema_form,
                                             contributor_name, parent_key)
            elif key == "relation":
                related_identifier = val.get("relatedIdentifier")
                if related_identifier:
                    key_data = get_key_value(schema_form,
                                             related_identifier, parent_key)
            else:
                key_data = get_key_value(schema_form, val, parent_key)
            if key_data:
                if isinstance(result.get(key), list):
                    result[key].append({key: key_data})
                elif result.get(key):
                    result[key] = [{key: result.get(key)}, {key: key_data}]
                else:
                    result[key] = key_data
        elif isinstance(val, list):
            for mapping_data in val:
                get_autofill_key_tree(schema_form, mapping_data, result)

    return result


def get_key_value(schema_form, val, parent_key):
    """Get key value.

    :param schema_form: Schema form
    :param val: Schema form value
    :param parent_key: The parent key
    :return: The key value
    """
    key_data = dict()
    if val.get("@value") is not None:
        value_key = val.get('@value')
        key_data['@value'] = get_autofill_key_path(
            schema_form,
            parent_key,
            value_key
        ).get('key')

    if val.get("@attributes") is not None:
        value_key = val.get('@attributes')
        if value_key.get("xml:lang") is not None:
            key_data['@language'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("xml:lang")
            ).get('key')
        elif value_key.get("identifierType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("identifierType")
            ).get('key')
        elif value_key.get("descriptionType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("descriptionType")
            ).get('key')
        elif value_key.get("subjectScheme") is not None:
            key_data['@scheme'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("subjectScheme")
            ).get('key')
        elif value_key.get("subjectURI") is not None:
            key_data['@URI'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("subjectURI")
            ).get('key')
        elif value_key.get("dateType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("dateType")
            ).get('key')

    return key_data


def get_autofill_key_path(schema_form, parent_key, child_key):
    """Get auto fill key path.

    :param schema_form: Schema form
    :param parent_key: Parent key
    :param child_key: Child key
    :return: The key path
    """
    result = dict()
    key_result = ''
    existed = False
    try:
        for item in schema_form:
            if item.get("key") == parent_key:
                items_list = item.get("items")
                for item_data in items_list:
                    if existed:
                        break
                    existed, key_result = get_specific_key_path(
                        child_key.split('.'), item_data)
        result['key'] = key_result
    except Exception as e:
        current_app.logger.debug(e)
        result['key'] = None
        result['error'] = str(e)

    return result


def get_specific_key_path(des_key, form):
    """Get specific path of des_key on form.

    @param des_key: Destination key
    @param form: The form key list
    @return: Existed flag and path result
    """
    existed = False
    path_result = None
    if isinstance(form, dict):
        list_keys = form.get("key", None)
        if list_keys:
            list_keys = list_keys.replace('[]', '').split('.')
            # Always remove the first element because it is parents key
            list_keys.pop(0)
            if set(list_keys) == set(des_key):
                existed = True
        if existed:
            return existed, form.get("key")
        elif not existed and form.get("items"):
            return get_specific_key_path(des_key, form.get("items"))
    elif isinstance(form, list):
        for child_form in form:
            if existed:
                break
            existed, path_result = get_specific_key_path(des_key, child_form)
    return existed, path_result


def build_record_model(item_autofill_key, api_data):
    """Build record record_model.

    :param item_autofill_key: Item auto-fill key
    :param api_data: Api data
    :return: Record model list
    """
    def _build_record_model(_api_data, _item_autofill_key, _record_model_lst):
        """Build record model.

        @param _api_data: Api data
        @param _item_autofill_key: Item auto-fill key
        @param _record_model_lst: Record model list
        """
        for k, v in _item_autofill_key.items():
            data_model = {}
            api_autofill_data = _api_data.get(k)
            if not api_autofill_data:
                continue
            if isinstance(v, dict):
                build_form_model(data_model, v)
            elif isinstance(v, list):
                for mapping_data in v:
                    _build_record_model(_api_data, mapping_data,
                                        _record_model_lst)
            record_model = {}
            for key, value in data_model.items():
                merge_dict(record_model, value)
            is_multiple_data = is_multiple(record_model, api_autofill_data)
            fill_data(record_model, api_autofill_data, is_multiple_data)
            if record_model:
                _record_model_lst.append(record_model)

    record_model_lst = list()
    if not api_data or not item_autofill_key:
        return record_model_lst
    _build_record_model(api_data, item_autofill_key, record_model_lst)

    return record_model_lst


def build_model(form_model, form_key):
    """Build model.

    @param form_model:
    @param form_key:
    """
    child_model = {}
    if '[]' in form_key:
        form_key = form_key.replace("[]", "")
        child_model = []
    if isinstance(form_model, dict):
        form_model[form_key] = child_model
    else:
        form_model.append({form_key: child_model})


def build_form_model(form_model, form_key, autofill_key=None):
    """Build form model.

    @param form_model:
    @param form_key:
    @param autofill_key:
    """
    if isinstance(form_key, dict):
        for k, v in form_key.items():
            if isinstance(v, str) and v:
                arr = v.split('.')
                form_model[k] = {}
                build_form_model(form_model[k], arr, k)
    elif isinstance(form_key, list):
        if len(form_key) > 1:
            key = form_key.pop(0)
            build_model(form_model, key)
            key = key.replace("[]", "")
            if isinstance(form_model, dict):
                build_form_model(form_model[key], form_key,
                                 autofill_key)
            else:
                build_form_model(form_model[0].get(key), form_key,
                                 autofill_key)
        elif len(form_key) == 1:
            key = form_key.pop(0)
            if isinstance(form_model, list):
                form_model.append({key: autofill_key})
            elif isinstance(form_model, dict):
                form_model[key] = autofill_key


def merge_dict(original_dict, merged_dict, over_write=True):
    """Merge dictionary.

    @param original_dict: the original dictionary.
    @param merged_dict: the merged dictionary.
    @param over_write: the over write flag.
    """
    if isinstance(original_dict, list) and isinstance(merged_dict, list):
        for data in merged_dict:
            for data_1 in original_dict:
                merge_dict(data_1, data)
    elif isinstance(original_dict, dict) and isinstance(merged_dict, dict):
        for key in merged_dict:
            if key in original_dict:
                if isinstance(original_dict[key], (dict, list)) and isinstance(
                        merged_dict[key], (dict, list)):
                    merge_dict(original_dict[key], merged_dict[key])
                elif original_dict[key] == merged_dict[key]:
                    continue
                else:
                    if over_write:
                        merged_dict[key] = original_dict[key]
                    else:
                        current_app.logger.error('Conflict at "{}"'.format(key))
            else:
                original_dict[key] = merged_dict[key]


def deepcopy(original_object, new_object):
    """Copy dictionary object.

    @param original_object: the original object.
    @param new_object: the new object.
    @return:
    """
    import copy
    if isinstance(original_object, dict):
        for k, v in original_object.items():
            if not isinstance(new_object, (dict, list)):
                new_object = {}
                deepcopy(copy.deepcopy(v), new_object[k])
            else:
                new_object[k] = copy.deepcopy(v)
    elif isinstance(original_object, list):
        for original_data in original_object:
            if isinstance(original_data, (dict, list)):
                deepcopy(copy.deepcopy(original_data), new_object)
    else:
        return


def fill_data(form_model, autofill_data, is_multiple_data=False):
    """Fill data to form model.

    @param form_model: the form model.
    @param autofill_data: the autofill data
    @param is_multiple_data: multiple flag.
    """
    if isinstance(autofill_data, list):
        if is_multiple_data:
            key = list(form_model.keys())[0]
            model_clone = {}
            deepcopy(form_model[key][0], model_clone)
            form_model[key] = []
            for data in autofill_data:
                model = {}
                deepcopy(model_clone, model)
                fill_data(model, data)
                form_model[key].append(model.copy())
        else:
            fill_data(form_model, autofill_data[0])
    elif isinstance(autofill_data, dict):
        if isinstance(form_model, dict):
            for k, v in form_model.items():
                if isinstance(v, str):
                    form_model[k] = autofill_data.get(v, '')
                else:
                    fill_data(v, autofill_data)
        elif isinstance(form_model, list):
            for v in form_model:
                fill_data(v, autofill_data)
    else:
        return


def is_multiple(form_model, autofill_data):
    """Check form model.

    @param form_model: Form model data.
    @param autofill_data: Autofill data.
    @return: True if form model can auto-fill with multiple data.
    """
    if isinstance(autofill_data, list) and len(autofill_data) > 1:
        for key in form_model:
            return isinstance(form_model[key], list)
    else:
        return False


def get_workflow_journal(activity_id):
    """Get workflow journal data.

    :param activity_id: The identify of Activity.
    :return: Workflow journal data
    """
    journal_data = None
    with db.session.no_autoflush:
        journal = ActionJournal.query.filter_by(
            activity_id=activity_id).one_or_none()
        if journal:
            journal_data = journal.action_journal
    return journal_data


def convert_crossref_xml_data_to_dictionary(api_data):
    """Convert CrossRef XML data to dictionary.

    :param api_data: CrossRef xml data
    :return: CrossRef data is converted to dictionary.
    """
    rtn_data = {}
    result = api_data.split('\n')[1]
    root = etree.fromstring(result)
    crossref_xml_data_keys = config.WEKO_ITEMS_AUTOFILL_CROSSREF_XML_DATA_KEYS
    contributor_roles = config.WEKO_ITEMS_AUTOFILL_CROSSREF_CONTRIBUTOR
    for elem in root.getiterator():
        if etree.QName(elem).localname in crossref_xml_data_keys:
            if etree.QName(elem).localname == "contributor" or etree.QName(
                    elem).localname == "organization":
                _get_contributor_and_author_names(elem, contributor_roles,
                                                  rtn_data)
            elif etree.QName(elem).localname == "year":
                if 'media_type' in elem.attrib \
                        and elem.attrib['media_type'] == "print":
                    rtn_data.update({etree.QName(elem).localname: elem.text})
            elif etree.QName(elem).localname in ["issn", "isbn"]:
                if 'type' in elem.attrib \
                        and elem.attrib['type'] == "print":
                    rtn_data.update({etree.QName(elem).localname: elem.text})
            else:
                rtn_data.update({etree.QName(elem).localname: elem.text})
    return rtn_data


def _get_contributor_and_author_names(elem, contributor_roles, rtn_data):
    """Get contributor and author name from API response data.

    @param elem: API data
    @param contributor_roles: Contributor roles
    @param rtn_data: Return data
    """
    temp = {}
    for element in elem.getiterator():
        if etree.QName(element).localname == 'given_name':
            temp.update({"given": element.text})
        if etree.QName(element).localname == 'surname':
            temp.update({"family": element.text})
    if elem.attrib['contributor_role'] in contributor_roles:
        if "contributor" in rtn_data:
            rtn_data["contributor"].append(temp)
        else:
            rtn_data.update({"contributor": [temp]})
    else:
        if "author" in rtn_data:
            rtn_data["author"].append(temp)
        else:
            rtn_data.update({"author": [temp]})
