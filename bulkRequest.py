#!/usr/bin/python

class BulkRequest(object):
    def __init__(self):
        print("creating BulkRequest")
        self.requests = []


    def numberOfActions(self) -> int:
        return len(self.requests)

    def add(self, request):
        self.requests.append(request)

    def getRequests(self):
        return self.requests


