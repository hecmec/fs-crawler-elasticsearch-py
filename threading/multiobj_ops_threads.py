import time

class SomeClass(object):
    def __init__(self):
        self.c=0

    def do(self):
        for i in range(100):
            time.sleep(0.01) # sleep makes the os continue another thread
            self.c = self.c + 1


        print( self.c)


import threading

threads = []


for _ in range(100):

    x = SomeClass()

    threading.Thread( target=x.do ).start()


for th in threads: 
    th.join() 

