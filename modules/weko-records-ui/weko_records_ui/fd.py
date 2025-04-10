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

"""Utilities for download file."""

import mimetypes
import unicodedata

from flask import abort, current_app, render_template, request
from flask_login import current_user
from invenio_files_rest import signals
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_files_rest.proxies import current_permission_factory
from invenio_files_rest.views import ObjectResource, check_permission, \
    file_downloaded
from invenio_records_files.utils import record_file_factory
from weko_deposit.api import WekoRecord
from weko_groups.api import Group
from weko_records.api import FilesMetadata, ItemsMetadata, ItemTypeProps, \
    ItemTypes, Mapping
from weko_records.serializers.utils import get_item_type_name, \
    get_item_type_name_id
from weko_user_profiles.models import UserProfile
from werkzeug.datastructures import Headers
from werkzeug.urls import url_quote

from .models import PDFCoverPageSettings
from .pdf import make_combined_pdf
from .permissions import check_original_pdf_download_permission, \
    file_permission_factory
from .utils import get_billing_file_download_permission, get_groups_price, \
    get_min_price_billing_file_download, is_billing_item


def weko_view_method(pid, record, template=None, **kwargs):
    r"""Display Weko view.

    Sends record_viewed signal and renders template.

    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :returns: The rendered template.
    """
    flst = FilesMetadata.get_records(pid.pid_value)
    frecord = []

    if len(flst) > 0:
        for fj in flst:
            frecord.append(fj.dumps())

    item_type = ItemTypes.get_by_id(id_=record['item_type_id'])
    item_type_info = "{}({})".format(item_type.item_type_name.name,
                                     item_type.tag)
    return render_template(
        template,
        pid=pid,
        record=record,
        files=frecord,
        item_type_info=item_type_info
    )


def prepare_response(pid_value, fd=True):
    """Prepare response data and header.

    :param pid_value:
    :param fd:
    :return:
    """
    fn = request.view_args.get("filename")

    flst = FilesMetadata.get_records(pid_value)
    for fj in flst:
        if fj.dumps().get("display_name") == fn:
            stream = fj.model.contents[:]
            displaytype = fj.model.json.get("displaytype")
            file_name = fj.model.json.get("file_name")
            break

    headers = Headers()
    headers['Content-Length'] = len(stream)
    try:
        filenames = {'filename': fn.encode('latin-1')}
    except UnicodeEncodeError:
        filenames = {'filename*': "UTF-8''%s" % url_quote(fn)}
        encoded_filename = (unicodedata.normalize('NFKD', fn)
                            .encode('latin-1', 'ignore'))
        if encoded_filename:
            filenames['filename'] = encoded_filename

    if fd:
        headers.add('Content-Disposition', 'attachment', **filenames)
        mimetype = 'application/octet-stream'
    else:
        headers['Content-Type'] = 'text/plain; charset=utf-8'
        headers.add('Content-Disposition', 'inline')
        mimetype = mimetypes.guess_type(request.view_args.get("filename"))[0]
        # if 'detail' in displaytype and '.pdf' in file_name:
        #     from PyPDF2.pdf import PdfFileWriter, PdfFileReader
        #     import io
        #     source = PdfFileReader(io.BytesIO(stream), strict=True)
        #     fp = source.getPage(0)
        #     writer = PdfFileWriter()
        #     writer.addPage(fp)
        #     f = io.BytesIO()
        #     writer.write(f)
        #     stream = f.getvalue()

    rv = current_app.response_class(
        stream,
        mimetype=mimetype,
        headers=headers,
        direct_passthrough=True,
    )

    return rv


def file_preview_ui(pid, record, _record_file_factory=None, **kwargs):
    """File preview view for a given record.

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:

    .. code-block:: python

        RECORDS_UI_ENDPOINTS = dict(
            recid=dict(
                # ...
                route='/records/<pid_value/file_preview/<filename>',
                view_imp='invenio_records_files.utils:file_preview_ui',
                record_class='invenio_records_files.api:Record',
            )
        )

    :param _record_file_factory:
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    return file_ui(
        pid,
        record,
        _record_file_factory,
        is_preview=True,
        **kwargs)


def file_download_ui(pid, record, _record_file_factory=None, **kwargs):
    """File download view for a given record.

    Plug this method into your ``RECORDS_UI_ENDPOINTS`` configuration:

    .. code-block:: python

        RECORDS_UI_ENDPOINTS = dict(
            recid=dict(
                # ...
                route='/records/<pid_value/files/<filename>',
                view_imp='invenio_records_files.utils:file_download_ui',
                record_class='invenio_records_files.api:Record',
            )
        )

    :param _record_file_factory:
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    return file_ui(
        pid,
        record,
        _record_file_factory,
        is_preview=False,
        **kwargs)


def file_ui(
        pid,
        record,
        _record_file_factory=None,
        is_preview=False,
        **kwargs):
    """File Ui.

    :param is_preview: Determine the type of event.
           True: file-preview, False: file-download
    :param _record_file_factory:
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The record metadata.
    """
    _record_file_factory = _record_file_factory or record_file_factory
    # Extract file from record.
    fileobj = _record_file_factory(
        pid, record, kwargs.get('filename')
    )

    if not fileobj:
        abort(404)

    obj = fileobj.obj

    # Check file contents permission
    if not file_permission_factory(record, fjson=fileobj).can():
        abort(403)

    # #Check permissions
    # ObjectResource.check_object_permission(obj)

    # Get user's language and defautl language for PDF coverpage.
    user_profile = UserProfile.get_by_userid(current_user.get_id())
    lang = user_profile.language if user_profile else 'en'

    add_signals_info(record, obj)
    """ Send file without its pdf cover page """

    try:
        pdfcoverpage_set_rec = PDFCoverPageSettings.find(1)
        coverpage_state = WekoRecord.get_record_cvs(pid.object_uuid)

        is_original = request.args.get('original') or False
        is_pdf = 'pdf' in fileobj.mimetype
        can_download_original_pdf = check_original_pdf_download_permission(
            record)

        convert_to_pdf = False
        if is_preview \
                and ('msword' in fileobj.mimetype
                     or 'vnd.ms' in fileobj.mimetype
                     or 'vnd.openxmlformats' in fileobj.mimetype):
            convert_to_pdf = True

        # if not pdf or cover page disabled: Download directly
        # if pdf and cover page enabled and has original in query param: check
        # permission (user roles)
        if is_pdf is False \
                or pdfcoverpage_set_rec is None \
                or pdfcoverpage_set_rec.avail == 'disable' \
                or coverpage_state is False \
                or (is_original and can_download_original_pdf):
            return ObjectResource.send_object(
                obj.bucket, obj,
                expected_chksum=fileobj.get('checksum'),
                logger_data={
                    'bucket_id': obj.bucket_id,
                    'pid_type': pid.pid_type,
                    'pid_value': pid.pid_value,
                },
                as_attachment=not is_preview,
                is_preview=is_preview,
                convert_to_pdf=convert_to_pdf
            )
    except AttributeError:
        return ObjectResource.send_object(
            obj.bucket, obj,
            expected_chksum=fileobj.get('checksum'),
            logger_data={
                'bucket_id': obj.bucket_id,
                'pid_type': pid.pid_type,
                'pid_value': pid.pid_value,
            },
            as_attachment=not is_preview,
            is_preview=is_preview
        )

    # Send file with its pdf cover page
    file_instance_record = FileInstance.query.filter_by(
        id=obj.file_id).first()

    # return obj_file_uri
    signals.file_downloaded.send(current_app._get_current_object(), obj=obj)
    return make_combined_pdf(pid, fileobj, obj, lang)


def add_signals_info(record, obj):
    """Add event signals info.

    Add user role, site license flag, item index list.

    :param record: the record metadate.
    :param obj: send object.
    """
    # Add user role info to send_obj

    userrole = 'guest'
    userid = 0
    user_groups = []
    if hasattr(current_user, 'id'):
        userid = current_user.id
        user_groups = Group.query_by_user(current_user).all()
        if len(current_user.roles) == 0:
            userrole = 'user'
        elif len(current_user.roles) == 1:
            userrole = current_user.roles[0].name
        else:
            max_power_role_id = 2147483646
            for r in current_user.roles:
                if max_power_role_id > r.id:
                    if max_power_role_id == 2147483646 or r.id > 0:
                        max_power_role_id = r.id
                        userrole = r.name
    obj.userrole = userrole
    obj.userid = userid

    # Add groups of current users
    groups = [{'group_id': g.id, 'group_name': g.name} for g in user_groups]
    obj.user_group_list = groups if groups else None

    # Check whether billing file or not
    obj.is_billing_item = is_billing_item(record['item_type_id'])

    # Add billing file price
    billing_file_price = ''
    if obj.is_billing_item:
        groups_price = get_groups_price(record)
        billing_files_permission = \
            get_billing_file_download_permission(groups_price)
        min_price_dict = \
            get_min_price_billing_file_download(groups_price,
                                                billing_files_permission)
        if isinstance(min_price_dict, dict):
            billing_file_price = min_price_dict.get(obj.key)
    obj.billing_file_price = billing_file_price

    # Add site license flag to send_obj
    obj.site_license_flag = True if hasattr(current_user, 'site_licese_flag') \
        else False
    obj.site_license_name = current_user.site_license_name \
        if hasattr(current_user, 'site_license_name') else ''

    # Add index list info to send_obj
    index_list = ''
    record_navs = record.navi
    if len(record_navs) > 0:
        for index in record_navs:
            index_list += index[3] + '|'
    obj.index_list = index_list[:len(index_list) - 1]

    # Add item info to send_obj
    obj.item_title = record['item_title']
    obj.item_id = record['_deposit']['id']
