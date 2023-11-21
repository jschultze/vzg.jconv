# -*- coding: utf-8 -*-
"""Beschreibung

##############################################################################
#
# Copyright (c) 2023 Verbundzentrale des GBV.
# All Rights Reserved.
#
##############################################################################
"""

import datetime
import logging
from oaipmh.client import Client
from oaipmh.metadata import MetadataRegistry
from oaipmh.metadata import MetadataReader
from typing import Generator
from zope.interface import implementer
from vzg.jconv.interfaces import IArchive


__author__ = """Marc-J. Tegethoff <tegethoff@gbv.de>"""
__docformat__ = 'plaintext'


class OAIClient(Client):

    def __init__(self,
                 base_url: str,
                 metadata_registry: MetadataRegistry = None,
                 credentials: str = None,
                 local_file: bool = False,
                 force_http_get: bool = False):

        super().__init__(base_url,
                         metadata_registry,
                         credentials=credentials,
                         local_file=local_file,
                         force_http_get=force_http_get)

        self.__num_records__ = '0'

    def ListRecords_impl(self, args, tree):
        logger = logging.getLogger(__name__)

        namespaces = {"oai": "http://www.openarchives.org/OAI/2.0/",
                      "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/"}

        stm = "string(./oai:ListRecords/oai:resumptionToken/@completeListSize)"

        try:
            self.__num_records__ = tree.xpath(stm, namespaces=namespaces)
        except Exception:
            logger.error("No resumptionToken", exc_info=True)

        return super().ListRecords_impl(args, tree)


@implementer(IArchive)
class ArchiveOAIDC:

    def __init__(self,
                 baseurl: str,
                 from_date: datetime.datetime,
                 until_date: datetime.datetime,
                 local_file: bool = False,
                 converter_kwargs: dict = {}) -> None:
        self.baseurl = baseurl
        self.from_date = from_date
        self.until_date = until_date
        self.local_file = local_file
        self.converter_kwargs = converter_kwargs

        self.metadataPrefix = "oai_dc"
        oai_dc_reader = MetadataReader(
            fields={
                'title':       ('textList', 'oai_dc:dc/dc:title/text()'),
                'creator':     ('textList', 'oai_dc:dc/dc:creator/text()'),
                'subject':     ('textList', 'oai_dc:dc/dc:subject/text()'),
                'description': ('textList', 'oai_dc:dc/dc:description/text()'),
                'description_language': ('textList', 'oai_dc:dc/dc:description/@xml:lang'),
                'publisher':   ('textList', 'oai_dc:dc/dc:publisher/text()'),
                'contributor': ('textList', 'oai_dc:dc/dc:contributor/text()'),
                'date':        ('textList', 'oai_dc:dc/dc:date/text()'),
                'type':        ('textList', 'oai_dc:dc/dc:type/text()'),
                'format':      ('textList', 'oai_dc:dc/dc:format/text()'),
                'identifier':  ('textList', 'oai_dc:dc/dc:identifier/text()'),
                'source':      ('textList', 'oai_dc:dc/dc:source/text()'),
                'language':    ('textList', 'oai_dc:dc/dc:language/text()'),
                'relation':    ('textList', 'oai_dc:dc/dc:relation/text()'),
                'coverage':    ('textList', 'oai_dc:dc/dc:coverage/text()'),
                'rights':      ('textList', 'oai_dc:dc/dc:rights/text()')
            },
            namespaces={
                'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                'dc': 'http://purl.org/dc/elements/1.1/'}
        )

        self.registry = MetadataRegistry()
        self.registry.registerReader('oai_dc', oai_dc_reader)

        self.__article_type__ = ['info:eu-repo/semantics/article', 'article']

    @property
    def converters(self) -> Generator[dict, None, None]:
        client = OAIClient(self.baseurl,
                           self.registry,
                           local_file=self.local_file)

        for header, record, other in client.listRecords(metadataPrefix=self.metadataPrefix,
                                                        from_=self.from_date,
                                                        until=self.until_date):
            if not record:
                continue

            if record.getField("type") != self.__article_type__:
                continue

            yield record

    @property
    def num_files(self) -> int:
        """Number of articles"""
        client = OAIClient(self.baseurl,
                           self.registry,
                           local_file=self.local_file)
        client.listRecords(metadataPrefix=self.metadataPrefix,
                           from_=self.from_date,
                           until=self.until_date)

        return int(client.__num_records__)
