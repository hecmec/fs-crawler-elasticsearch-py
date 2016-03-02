#!/usr/bin/python

from elasticsearch_dsl import DocType, String, Date, Integer, Attachment, Nested
import hashlib
import tools


class FileResource(DocType):
    '''
    A file resource is a representation of a file found by the crawler
    '''
    # the content in base64
    content = String(analyzer="snowball")
    content_length = Integer()

    meta_title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    meta_author = String(analyzer="snowball")
    # for multi: creator, last-author, meta-autor etc....
    meta_authors = String(analyzer="snowball")
    meta_keywords = String(analyzer="snowball")
    meta_content_type = String(analyzer="snowball")
    meta_content_encoding = String(index='not_analyzed')
    meta_language = String(index='not_analyzed')

    # datetime of last indexing
    indexing_date = Date()

    # hashed directory, the container
    file_dir_hash = String(index='not_analyzed')
    # c:\eins  - parent directory of the file or dir (in order to search if it is still there
    file_dir_path = String(index='not_analyzed')
    # bla.txt
    file_name = String()
    # c:\eins\bla.txt
    file_uri = String(index='not_analyzed')

    file_creation_date = Date()
    file_modification_date = Date()
    file_size = Integer()

    # we use the static init method on DocType to pass the index

    #class Meta:
    #    index = ''

    #def __init__(self, index):
    #    if(index):
    #        super({"index" : index})


    def save(self, ** kwargs):
        # set id as uriHash
        self.meta.id = tools.get_hash(self.file_uri)
        return super(FileResource, self).save(** kwargs)

