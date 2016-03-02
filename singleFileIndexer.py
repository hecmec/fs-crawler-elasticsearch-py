#!/usr/bin/python

from os import path
from datetime import datetime

import hashlib
import base64 

from elasticsearch_client import ElasticSearchClient
from tika_client import TikaClient
import threading
import logging

#class FileIndexer(object):
#    """description of class"""

#    def __init__(self, path, file_name, config, counter):
#        self.lock = threading.Lock()    
#        self.path = path
#        self.file_name = file_name
#        self.config = config
#        self.counter = counter


def process_file(esIndex, path, file_name, config, counter):

    try:
        tika = TikaClient(config["fs"])
        parsed = tika.parse_file(path, file_name)

        print("----> pf %s %s" % (path, file_name))

        es = ElasticSearchClient(esIndex)
        #print("singleFileIndexer.process_file ES_client created")

        ok = es.process_file(path, file_name, parsed)

        if(ok):
            #print("singleFileIndexer.process_file ----- ok")

            counter["files_indexed"] = counter["files_indexed"] +1

            idf = counter["files_indexed"]
            skf = counter["files_skipped"]
            idd = counter["dirs_indexed"]
            skd = counter["dirs_skipped"]
            if( (idf > 0 and idf % 100 == 0) or (idd > 0 and idd % 100 == 0) ):
                print("\n\n\n")
                print("------------------------------------------------------------ indexed %i files" % idf)
                print("------------------------------------------------------------ skipped %i files" % skf)
                print("------------------------------------------------------------ indexed %i directories" % idd)
                print("------------------------------------------------------------ skipped %i directories \n\n\n" % skd)


            return True

        else:
            #print("singleFileIndexer.process_file ----- something went wrong")
            return False
    except Exception as ex:
        logging.exception(ex)


