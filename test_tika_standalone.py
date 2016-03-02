
import tika
from tika import parser
from os import path

import sys
import codecs


def parse_files(file_name):
    print("parsing file : % \n", file_name) 

    parsed = parser.from_file(file_name)


    print("meta-data:\n")
    print(parsed["metadata"])
    print("content:\n")
    content = parsed["content"]
    c2 = content.encode('utf-8').strip()
    print(c2)
    print("\n\n");


# Optionally, you can pass Tika server URL along with the call
# what's useful for multi-instance execution or when Tika is dockerzed/linked
#parsed = parser.from_file(file_name, 'http://tika:9998/tika')
#string_parsed = parser.from_buffer('Good evening, Dave', 'http://tika:9998/tika')

#import tika
#tika.initVM()
#from tika import parser

#parsed = parser.from_file(r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\test_root_1.txt')

#print(parsed["metadata"])
#print(parsed["content"])


if __name__ == "__main__":
    file_names = [
        r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\test_root_1.txt',
        r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\Manifeste Agile.doc',
        r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\pdf-sample.pdf',
        r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\test_root_1.doc',
        r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\test_root_1.docx',
        r'C:\Projets\elasticsearch-2.2.0\jpe_testdata\test_version.odt'
    ]

    for fn in file_names:
        parse_files(fn)
