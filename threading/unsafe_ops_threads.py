import time

class SomeClass(object):
    def __init__(self,c):
        self.c=c

    def inc(self):
        new = self.c+1 
        # if the thread is interrupted by another inc() call its result is wrong
        time.sleep(0.001) # sleep makes the os continue another thread
        self.c = new


x = SomeClass(0)

import threading

threads = []


for _ in range(1000):
    threading.Thread(target=x.inc).start()


for th in threads: 
    th.join() 

print( x.c) # ~370 here, instead of 1000