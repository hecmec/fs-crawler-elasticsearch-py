#!/usr/bin/python

import threading
import hashlib


def get_hash(s:str):
    '''
    this gets a sha1 hash for any given string
    '''
    result_hash = ""
    lock = threading.Lock()
    try:
        lock.acquire()
        s_enc = s.encode('utf-8')
        result_hash = hashlib.sha1(s_enc).hexdigest()

    except Exception as ex:
        print(ex)
        traceback.print_exc(file=sys.stdout)

    finally:
        if(lock.locked()):
            lock.release()

    return result_hash
