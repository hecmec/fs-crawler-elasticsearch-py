#!/usr/bin/python

import sys
import threading
import argparse
import os
import time
import datetime

import json
import fnmatch
import traceback

import singleFileIndexer
from elasticsearch_dsl.connections import connections
from elasticsearch_client import ElasticSearchClient
from tika_client import TikaClient
from fileResource import FileResource

import logging

sleep_ms = lambda x: time.sleep(x/1000.0)

'''
This is inspired by David Pilatos fsCrawler

'''

def main():
    '''
    Load the contents of all crawlable files in a directory recursively and bulk index them into ElasticSearch
    https://github.com/rstruber/disk-to-elasticsearch-crawler/blob/master/__main__.py
    '''
    print("Getting configuration\n")
    with open('config.json', 'r') as f:
        config = json.load(f)


    fsConfig = config["fs"]
    esConfig = config["elasticsearch"]

    # start tika server in main thread
    print("Starting up Tika server ...\n")

    tika = TikaClient(fsConfig)
    tika.startServer()

    if(esConfig and esConfig["nodes"]):
        esNodes = esConfig["nodes"]
        esIndex = esConfig["index"]

        connections.create_connection(hosts=esNodes)
        #print(connections.get_connection().cluster.health())

        # update mapping
        FileResource.init(index=esIndex)
        print("updating index %s" % esIndex)

    print("Connecting to ElasticSearch server\n")
    es = ElasticSearchClient(esIndex)

    last_scan_date = datetime.datetime(2012,2,20,10,42,55)
    globPattern = config["fs"]["includes"]
    root_path =  config["fs"]["url"]
    threadLimit =   config["fs"]["threads"]

    indexed_file_count = 0
    counter = {"files_indexed" : 0, "files_skipped" : 0,  "dirs_indexed" : 0, "dirs_skipped" : 0 }
    threads = [] 
    cnt = 0
    multithread = False

    print("Walking file-tree\n")

    for path, dirs, files in os.walk(root_path):
             # filter out Sauvekiveu
        dirs[:] = [d for d in dirs if is_indexable_dir(d)]

        #get a filter function for files
        is_indexable_file = get_isindexable_func(path, globPattern, last_scan_date)

        for file_name in filter(is_indexable_file, files):
            index_file(es, multithread, path, file_name, config, counter)


        for dir_name in dirs:
            try:

                dir = es.get_dir_by_name(path, dir_name)
                dir_has_changed = False

                if(dir):
                    dir_path = os.path.join(path, dir_name)
                    dir_has_changed = has_changed(dir_path, dir.indexing_date)

                if(not dir or dir_has_changed):
                    print("====> pd %s %s" % (path, dir_name))
                    counter["dirs_indexed"] = counter["dirs_indexed"] +1

                    es.process_dir(path, dir_name)
                else:
                    print('/',end="",flush=True)
                    counter["dirs_skipped"] = counter["dirs_skipped"] +1

            except Exception as ex:
                logging.exception(ex)
                print("\nGeneral error in fs_crawler while indexing a file.")


    print("\n*******************************\n")
    print("\n FINISHED \n")    
    print("indexed %i files" % indexed_file_count)


def index_file(es, multithread, path, file_name, config, counter):
    try:
        file = es.get_file_by_name(path, file_name)
        file_has_changed = False
        if(file):
            file_path = os.path.join(path, file_name)
            file_has_changed =  has_changed(file_path, file.indexing_date)

        if(not file or file_has_changed):
            
            if(multithread):
                while threading.activeCount() >= threadLimit:
                    sleep_ms(1000) #  sleep while max threads are currently running
                    print("waiting")

                t = threading.Thread(
                    target=singleFileIndexer.process_file,
                    args=(es.index, path, file_name, config, counter)
                )
                #threads.append(t)
                t.start()

            else:
                singleFileIndexer.process_file(es.index, path, file_name, config, counter)

        # not a file or has not changed, then skip it
        else:
            print('.',end="",flush=True)
            counter["files_skipped"] = counter["files_skipped"] +1


    except Exception as ex:
        logging.exception(ex)
        print("\nGeneral error in fs_crawler while indexing a file.")

def get_isindexable_func(path:str, globPattern, last_scan_date:datetime):
    ''' create a closure for the date argument'''
    def is_indexable_file_func(file_name):
        ''' all conditions '''
        file_path = os.path.join(path, file_name)

        isIndexable = has_correctExtension(file_name, globPattern) and has_good_size(file_path) and (has_changed(file_path, last_scan_date) or is_new(file_path, last_scan_date))
        return isIndexable

    return is_indexable_file_func

def has_good_size(file_path:str):
    # get size
    try:
        size = os.path.getsize(file_path)
        # bigger than 0 and smaller than 100 Mbyte
        if(size > 100000000):
            return False
            print("file too big \n")
        elif(size == 0):
            return False
            print("file is empty \n")
        else:
            return True

    except Exception as e:
        logging.exception(e)
        print("Error in fs_crawler.has_good_size")

def has_correctExtension(file_name:str, globPattern):
    '''returns true if the fileName indicates a indexable file'''
    is_match = False

    try:
        is_match = any(fnmatch.fnmatch(file_name, pat) for pat in globPattern)

    except Exception as e:
        logging.exception(e)
        print("Error in fs_crawler.has_correctExtension")

    return is_match

def has_changed(file_path:str, last_scan_date:datetime):
    ''' file or directory has been modified since last scan
        directory mtime changes if a file is modified or added or deleted
    '''
    has_changed = False

    try:
        last_update = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        has_changed = last_update > last_scan_date
    except Exception as e:
        logging.exception(e)
        print("cannot get getmtime")
        #traceback.print_exc(file=sys.stdout)

    return has_changed


def is_new(file_path:str, last_scan_date:datetime):
    ''' file is new '''
    has_been_created = False

    try:
        created_at = datetime.datetime.fromtimestamp(os.path.getctime(file_path))
        has_been_created = created_at > last_scan_date
    except Exception as e:
        logging.exception(e)
        print('cannot get is news')

    return has_been_created

def is_indexable_dir(dir:str):
    result = dir.lower().find("sauvekiveu") < 0
    return result


if __name__ == "__main__":

    logging.basicConfig(filename='es_crawler_err.log',level=logging.WARNING)

    main()



#if __name__ == "__main__":
#    args = argparse.ArgumentParser(description='Loads the contents of all crawlable files in a directory')
#    args.add_argument('--path', default="", type=str, help='Path to the directory to traverse')
#    args.add_argument('-t', '--threads', default=10, type=int, help='Max number of threads (default: 10)')
#    parsed_args = args.parse_args()

#    path = parsed_args.path if parsed_args.path else "C:\Projets\elasticsearch-2.2.0\jpe_testdata" 

#    main(path, parsed_args.threads)