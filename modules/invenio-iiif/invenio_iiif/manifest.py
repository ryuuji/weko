# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 Esteban J. G. Gabancho.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""IIIF Presentation API generation and helper functions."""

import urllib.parse

from flask import current_app,request
from flask_iiif.api import IIIFImageAPIWrapper
from flask_iiif.restful import current_iiif
from iiif_prezi.factory import Image as PreziImage
from iiif_prezi.factory import ManifestFactory as PrezyManifestFactory
from invenio_files_rest.models import ObjectVersion
from invenio_previewer.api import PreviewFile
from uritools import uricompose

from .previewer import can_preview
from .utils import iiif_image_key


class IIIFMetadata(dict):
    """IIIF Metadata extraction default class."""

    def __init__(self, record, **kwargs):
        """Initialize IIIF metadata."""
        self._record = record
        self.update(kwargs)
        self.extract_metadata()

    def extract_metadata(self):
        """Extract metadata and update self with the values."""
        # TODO


class IIIFManifest(object):
    """."""

    def __init__(self, record, metadata_class=None, extra_meatadata=None):
        """Initialize manifest."""
        self.record = record
        metadata_class = metadata_class if metadata_class else IIIFMetadata
        extra_meatadata = extra_meatadata if extra_meatadata else {}
        current_app.config['IIIF_API_SERVER']=request.url_root 
        factory = ManifestFactory(
            mdbase=current_app.config['IIIF_API_SERVER'],
            imgbase=urllib.parse.urljoin(
                current_app.config['IIIF_API_SERVER'],
                '{}v2'.format(current_app.config['IIIF_UI_URL']),
            ),
        )
        # FIXME: defaults?
        factory.set_iiif_image_info(2.0, 2)
        self.manifest = factory.manifest(
            ident="identifier/manifest", label=self.record['title']
        )
        self.manifest.description = self.record['title']
        self.manifest.viewingDirection = 'left-to-right'
        self.manifest.set_metadata(
            dict(metadata_class(record, **extra_meatadata))  # FIXME prezi!?!?!
        )

    def dumps(self):
        """Generate IIIF manifest using the IIIF Image API."""
        bucket = ''
        if '_buckets' in self.record:
            if 'deposit' in self.record['_buckets']:
              bucket = self.record['_buckets']['deposit']

        images = [
            obj
            for obj in ObjectVersion.get_by_bucket(bucket).all()
            if can_preview(PreviewFile(None, None, obj))
        ]

        if not images:
            return {}  # Didn't find any image inside the bucket

        sequence = self.manifest.sequence()
        for page, image in enumerate(images):
            canvas = sequence.canvas(
                ident=f'page-{page}', label=f'page-{page}'
            )
            canvas.set_image_annotation(iiif_image_key(image), iiif=True)
            # anno = canvas.annotation()
            # image = ano.image(iiif_image_key(image), iiif=True)
            # image.set_hw_from_iiif()
            # canvas.height = img.height
            # canvas.width = img.width

        return self.manifest.toJSON(top=True)


# IIIF-Prezi patches


class ManifestFactory(PrezyManifestFactory):
    """."""

    def image(self, ident, label="", iiif=False, region='full', size='full'):
        """Create an Image."""
        if not ident:
            raise RequirementError(
                "'Images must have a real identity "
                "(Image['@id'] cannot be empty)'"
            )
        return Image(self, ident, label, iiif, region, size)


class Image(PreziImage):
    """."""

    def set_hw_from_iiif(self):
        """."""
        cache_handler = current_iiif.cache()
        bucket_id, version_id, key = self._identifier.split(':')

        # Check if its cached
        cached = cache_handler.get(key)
        if cached:
            width, height = map(int, cached.split(','))
        else:
            data = current_iiif.uuid_to_image_opener(self._identifier)
            image = IIIFImageAPIWrapper.open_image(data)
            width, height = image.size()
            # if should_cache(request.args):
            #     cache_handler.set(key, "{0},{1}".format(width, height))

            self.height = int(height)
            self.width = int(width)
