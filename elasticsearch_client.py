#!/usr/bin/python

from datetime import datetime
from os import path
import sys
import hashlib
import base64 
import traceback
import threading
import tools
import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import DocType, String, Date, Integer
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.serializer import serializer

from elasticsearch_dsl import Attachment
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch

from bulkRequest import BulkRequest
from articleTest import ArticleTest
from fileResource import FileResource
from dirResource import DirResource

class ElasticSearchClient(object):
    """description of class"""

    def __init__(self, index):
        self.lock = threading.Lock()
        self.index = index

    def process_file(self, dir_path:str, file_name:str, parsed):
        '''
        indexes this file
        '''
        if(not dir_path or not file_name or not parsed):
            return False

        file_path = path.join(dir_path, file_name)
        #print("--- ElasticSearchClient process_file: full dir path %s" % file_path)

        try:
            modification_date = path.getmtime(file_path)
            creation_date = path.getctime(file_path)
            file_size = path.getsize(file_path)
            #is_file = path.isfile(file_path)
            #is_dir = path.isdir(file_path)

            dirEnc = dir_path.encode('utf-8')
            dirSha1 = hashlib.sha1(dirEnc).hexdigest()

            metadata = parsed["metadata"] if "metadata" in parsed else None
            content = parsed["content"] if "content" in parsed else None
            cleaned_content = parsed["cleaned_content"] if "cleaned_content" in parsed else None

            if(not metadata or not content or not cleaned_content):
                return False

            # content
            #FileResource.init(index=esIndex)
            res = FileResource(meta={'index': self.index})
            i = res._get_index()
            
            #contB64 = base64.b64encode(cleaned_content)
            #res.content = contB64.decode("utf-8") 
            res.content = cleaned_content.decode("utf-8") 
            res.content_length = len(res.content)

            if(metadata):
                res.meta_title = metadata["title"]                  if "title" in metadata else ""
                res.meta_author = self.get_meta_author(metadata)
                res.meta_keywords = metadata["Keywords"]            if "Keywords" in metadata else ""
                #res.meta_content_type = metadata["Content-Type"]    if "Content-Type" in metadata else ""
                res.meta_content_type = self.get_content_type(metadata)
                res.meta_content_encoding = metadata["Content-Encoding"] if "Content-Encoding" in metadata else ""
                res.meta_language = parsed["lang"]                  if "lang" in parsed else ""

            res.indexing_date = datetime.now()
            res.file_dir_hash = dirSha1
            res.file_dir_path = dir_path
            res.file_name = file_name
            res.file_uri = file_path
            res.file_creation_date = datetime.fromtimestamp(creation_date)
            res.file_modification_date = datetime.fromtimestamp(modification_date)
            res.file_size = file_size

            res.save()
            return True

        except Exception as e:
            logging.exception(e)
            print("error in process_file")
            #traceback.print_exc(file=sys.stdout)
            return False


    def get_meta_author(self, metadata):
        result = ""

        authorList = []
        if("Author" in metadata):
            authorList.append(metadata["Author"])
        if("meta:author" in metadata):
            authorList.append(metadata["meta:author"])
        if("Last-Author" in metadata):
            authorList.append(metadata["Last-Author"])
        if("meta:last-author" in metadata):
            authorList.append(metadata["meta:last-author"])
        if("creator" in metadata):
            authorList.append(metadata["creator"])
        if("meta:creator" in metadata):
            authorList.append(metadata["meta:creator"])
        if("dc:creator" in metadata):
            authorList.append(metadata["dc:creator"])

        a_set = set(self.flatten(authorList))
        f_set = [item for item in a_set if item.lower().find("microsoft") < 0 ]
        result = str.join(", ", f_set)

        return result

    def get_content_type(self, metadata):
        result = self.get_unique_joined_string(metadata, "Content-Type", ", ")
        return result

    def get_unique_joined_string(self, data, field_name:str, separator:str):
        result = ""

        if(field_name in data):
            val = data[field_name]  

            if(isinstance(val, list)):
                a_set = set(flatten(val))
                result = str.join(separator, a_set)
            else:
                result = val
        
        return result


    def flatten(self, foo):
        for x in foo:
            if hasattr(x, '__iter__') and not isinstance(x, str):
                for y in flatten(x):
                    yield y
            else:
                yield x

    def process_dir(self, dir_path:str, dir_name:str):
        '''
        indexes this directory
        we keep directories in order to find them on delete
        '''
        full_dir_path = path.join(dir_path, dir_name)
        #print("process_dir: full dir path %s" % full_dir_path)

        try:
            full_dir_path = path.join(dir_path, dir_name)

            # keep the parent directory, hash it for retrieval of children
            dirEnc = dir_path.encode('utf-8')
            dirSha1 = hashlib.sha1(dirEnc).hexdigest()

            res = DirResource(meta={'index': self.index})

            res.indexing_date = datetime.now()
            res.parent_dir_hash = dirSha1
            res.full_dir_path = full_dir_path
            res.path = dir_path
            res.dir = dir_name

            res.save()
            return True

        except Exception as e:
            logging.exception(e)
            print("Error in process_dir")
            return False

    def get_files_in_path(self, dir_path):
        ''' gets all es file names from es in a given path '''
        dir_hash = FileResource.get_hash(dir_path)
        #s = FileResource.search().query("match", path["hashdir"] = dir_hash)
        #s = FileResource.search().query("multi_match", query=dir_hash, fields=['path.hashdir'])
        # [{"query": {"match_all": {"index": "content_crawler", "body": {"query": {"term": {"path.hashdir": "b5844a9aba1536cc74682d8bfa28553b5dfd8a8a"}}}, "doc_type": "file_resource"}}
        s = Search().query(
            index = self.index, 
            doc_type= self.type, 
            body={"query": 
                { 
                    "term" : {
                        "file_dir_hash" : dir_hash
                    }
                }
            }
        )

        response = s.execute()

        files = []

        for hit in s:
            files.append(hit.file_uri)

        return files

    def get_file_by_name(self, dir_path, file_name):
        ''' 
        get a file from es by id
        id is full file name hash
        returns a FileResource object
        '''
        full_file_path = path.join(dir_path, file_name)

        return self.get_file_by_path(full_file_path)

    def get_file_by_path(self, file_path):
        ''' 
        get a file from es by id
        id is full file name hash
        returns a FileResource object
        '''
        if(not file_path):
            return None

        file = None
        try:
            id = tools.get_hash(file_path)
            file = FileResource.get(id, None, index=self.index)
        except Exception as ex:
            pass

        return file

    def get_dir_by_name(self, dir_path, dir_name):
        ''' 
        gets a dir from es by id (full_path hashed)
        '''
        if(not dir_path or not dir_name):
            return None

        full_path = path.join(dir_path, dir_name)

        dir = None
        try:
            id = tools.get_hash(full_path)
            dir = DirResource.get(id, None, index=self.index)
        except Exception as ex:
            pass

        return dir


    #def get_id_from_path(self, dir_path, file_name):
    #    id = FileResource.get_hash_id(dir_path, file_name)
    #    return id

    def delete_file(self, file_path):
        ''' deletes a file form es '''
        es_file = get_file_by_path(file_path)
        if(es_file):
            es_file.delete()
        else:
            print("Cannot delete, file does not exist: %s", file_path)


    def createIndex(self, index: str):
        print("creating index %s", index )

    def execBulkRequest(self, bulkRequest: BulkRequest):
        print("bulkRequest")

    def search(self, index: str, type: str, query: str):
        print("search")

    def isExistingType(self, index:str, type: str):
        print("isExistingType")

    def isExistingIndex(self, index:str):
        print("isExistingType")

    def testFileResource(self):

        dir = r"c:\eins\zwei\drei"
        file_name = "oscar_on_consistency.pdf"
        dirEnc = dir.encode('utf-8')
        dirSha1 = hashlib.sha1(dirEnc).hexdigest()
        full_path = path.join(dir, file_name)

        text = "Consistency is the last refuge of the unimaginative."
        textB64 = base64.b64encode(bytes(text, "utf-8"))
        textB64Str = textB64.decode("utf-8") 

        title = "oscar_on_consistency"
        content_type = "application/doc"


        # create the mappings in elasticsearch
        FileResource.init(index=self.index)

        res = FileResource(meta={'index': self.index})
        res.title = title
        res.content_start = text[:400]
        indexing_date = datetime.now()

        res.path = {
            'encoded' : dirSha1,
            'dir' : dir,
            'file_name' : file_name,
            'url' : r"file://" + full_path
        }

        res.file = {
            "_name" : file_name,
            "_content" : textB64Str,
            "_content_type" : content_type,
            #"_language" : "fr",
            "_title" : title,


            "_date" : datetime.now(),
            "_author" : "Oscar Wilde",
            "_keywords" : "oscar quotes ",
            # defaults to 100000
            "_indexed_chars" : 20000,
            "_detect_language" : True,
            "_content_length" : 123456,
        }

        # Consistency is the last refuge of the unimaginative.
        #"content" : "Q29uc2lzdGVuY3kgaXMgdGhlIGxhc3QgcmVmdWdlIG9mIHRoZSB1bmltYWdpbmF0aXZlLg=="   

        res.save()



