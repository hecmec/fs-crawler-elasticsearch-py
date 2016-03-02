#!/usr/bin/python

from elasticsearch_dsl import DocType, String, Date, Integer, Attachment, Nested
import hashlib
import tools

class DirResource(DocType):
    '''
    A dir resource is a representation of a dir found by the crawler
    '''

    # datetime of last indexing
    indexing_date = Date()

    # hashed directory (=dir), the containe/ parent  of this directory
    parent_dir_hash = String(index='not_analyzed')
    # 'eins/zwei/drei/toto'
    full_dir_path = String(index='not_analyzed')
    # 'eins/zwei/drei' in 'eins/zwei/drei/toto'  - parent directory of the file or dir (in order to search if it is still there
    path = String(index='not_analyzed')
    # 'toto' in 'eins/zwei/drei/toto'
    dir = String(index='not_analyzed')

    #class Meta:
    #    index = ''

    #def __init__(self, index):
    #    if(index):
    #        super({"index" : index})


    def save(self, ** kwargs):
        # set id as uriHash
        self.meta.id = tools.get_hash(self.full_dir_path)
        return super(DirResource, self).save(** kwargs)
