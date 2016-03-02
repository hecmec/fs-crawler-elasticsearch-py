import time
import threading

class SomeClass(object):
    def __init__(self,c):
        self.c=c
        self.lock = threading.Lock()

    def inc(self):
        self.lock.acquire()
        try:
            new = self.c+1 
            # if the thread is interrupted by another inc() call its result is wrong
            time.sleep(0.001) # sleep makes the os continue another thread
            self.c = new

        finally:
            self.lock.release()


x = SomeClass(0)


threads = []


for _ in range(1000):
   t= threading.Thread(target=x.inc)
   threads.append(t)
   t.start()


for th in threads: 
    th.join() 

print( x.c) # now there are 1000