#!/usr/bin/python

from elasticsearch_dsl import DocType, String, Date, Integer, Attachment, Nested
import hashlib

class FileResourceMA(DocType):
    '''
    A file resource is a representation of a file found by the crawler
    '''

    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})

    # first 400 chars in order to spot content 
    content_start = String(analyzer="snowball")

    # datetime of last indexing
    indexing_date = Date()

    #index.mapping.attachment.indexed_chars = 10000

    # this only works if the plugin mapper-attachments for ES 2.2.0 is properly installed
    file = Attachment(fields={
        "content": {"store" : "no", "type":"string" },
        "title" : {"store" : "yes", "type": "string"},
        "name" : {"store" : "yes", "type": "string"},
        "content_type" : {"store" : "yes", "type": "string"},
        "content_length" : {"store" : "yes", "type": "integer"},
        "language" : {"store" : "yes", "type": "string"}
        })

    path = Nested(
        properties={
            # hashed dir
            'dir_hash' : String(index='not_analyzed'),
            # c:\eins  - parent directory of the file or dir (in order to search if it is still there
            'dir_path' : String(index='not_analyzed'),
            # bla.txt
            'file_name' : String(index='not_analyzed'),
            # c:\eins\bla.txt
            'file_uri' : String(index='not_analyzed')
        }
    )

    class Meta:
        index = 'content_crawler'

    #def __init__(self, index):
    #    if(index):
    #        self.Meta.index = index


    def save(self, ** kwargs):
        # set id as uriHash
        self.meta.id = FileResource.get_hash(self.path["file_uri"])
        return super(FileResource, self).save(** kwargs)

    @staticmethod
    def get_hash_dir_name(dir_path:str, file_name:str):
        file_path = path.join(dir_path, file_name)
        file_path_enc = file_path.encode('utf-8')
        file_path_hash = hashlib.sha1(file_path_enc).hexdigest()
        return file_path_hash

    @staticmethod
    def get_hash(s:str):
        s_enc = s.encode('utf-8')
        s_hash = hashlib.sha1(s_enc).hexdigest()
        return s_hash


#GET /content_crawler/_mapping/file_resource
'''

'''