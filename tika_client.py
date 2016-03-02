#!/usr/bin/python
import sys
import traceback
import codecs
import tika
from tika import parser
from tika import tika
from os import path
import threading
import logging

class TikaClient(object):
    """description of class"""

    def __init__(self, fs_config):
        if(fs_config and fs_config["indexed_chars"]):
            self.indexed_chars = int(fs_config["indexed_chars"])
            self.lock = threading.Lock()

    def parse_file(self, dir_path, file_name):
        '''
        returns a parsed dict object
        it has the properties: "metadata", "content", "cleaned_content"
        '''
        join_ok = True
        file_path = path.join(dir_path, file_name)

        #print("\nTikaClient parsing file : %s \n" % file_path) 
        parse_result = self.parse_content(file_path)
        if(parse_result):
            parse_result["lang"] = self.parse_language(file_path)

        return parse_result


    def parse_content(self, file_path):
        ''' 
        extract content and metadata
        always returns an object       
        '''
        tn = threading.currentThread().getName()
        #print("TikaClient.parse_content of file %s in thread: %s" % (file_path, tn) )

        parsed = {}
        try:
            self.lock.acquire()
            parsed = parser.from_file(file_path)

            if(parsed and parsed["content"]):
                content = parsed["content"]
                content = content.strip()
                part_content = content[: self.indexed_chars]
                cleaned_content = part_content.encode('utf-8')
                parsed["cleaned_content"] = cleaned_content
            #else:
            #    print("TikaClient.parse_content NO CONTENT - of file %s in thread: %s" % (file_path, tn) )


        except Exception as ex:
            try:
                print("Could not parse content of file: %s" % file_path)
            except:
                print("houps parse_content")
            #print(ex)
            #traceback.print_exc(file=sys.stdout)

        finally:
            if(self.lock.locked()):
                self.lock.release()


        return parsed



    def parse_language(self, file_path):
        ''' 
        detect language of the file 
        returns a two letter language code
        returns 'fr' by default
        '''
        lang = 'fr'

        try:
            self.lock.acquire()

            langResp = tika.detectLang1('file', file_path)
            if(langResp and len(langResp) >= 2 and langResp[0] == 200 and langResp[1]):
                lang = langResp[1]


        except Exception as ex:
            try:
                print("Could not parse language of file: %s" % file_path)
            except:
                print("houps parse_language")

            #print(ex)
            #traceback.print_exc(file=sys.stdout)

        finally:
            if(self.lock.locked()):
                self.lock.release()



        return lang

    def startServer(self):
        tika.checkTikaServer()