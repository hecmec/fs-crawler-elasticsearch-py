#!/usr/bin/python

from elasticsearch_dsl import DocType, String, Date, Integer, Attachment


class ArticleTest(DocType):
    '''
    '''

    title = String(analyzer='snowball', fields={'raw': String(index='not_analyzed')})
    body = String(analyzer='snowball')
    #foobar = String(analyzer='standard')
    tags = String(index='not_analyzed')
    published_from = Date()
    lines = Integer()
    # this only works if the plugin mapper-attachments for ES 2.2.0 is properly installed
    my_attachment = Attachment()

    class Meta:
        index = 'blogtest'

    def save(self, ** kwargs):
        self.lines = len(self.body.split())
        return super(ArticleTest, self).save(** kwargs)

    def is_published(self):
        return datetime.now() > self.published_from



#GET /blogtest/_mapping/article_test
'''
{
   "blogtest": {
      "mappings": {
         "article_test": {
            "properties": {
               "body": {
                  "type": "string",
                  "analyzer": "snowball"
               },
               "foobar": {
                  "type": "string",
                  "analyzer": "standard"
               },
               "lines": {
                  "type": "integer"
               },
               "my_attachment": {
                  "type": "attachment",
                  "fields": {
                     "content": {
                        "type": "string"
                     },
                     "author": {
                        "type": "string"
                     },
                     "title": {
                        "type": "string"
                     },
                     "name": {
                        "type": "string"
                     },
                     "date": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                     },
                     "keywords": {
                        "type": "string"
                     },
                     "content_type": {
                        "type": "string"
                     },
                     "content_length": {
                        "type": "integer"
                     },
                     "language": {
                        "type": "string"
                     }
                  }
               },
               "published_from": {
                  "type": "date",
                  "format": "strict_date_optional_time||epoch_millis"
               },
               "tags": {
                  "type": "string",
                  "index": "not_analyzed"
               },
               "title": {
                  "type": "string",
                  "analyzer": "snowball",
                  "fields": {
                     "raw": {
                        "type": "string",
                        "index": "not_analyzed"
                     }
                  }
               }
            }
         }
      }
   }
}

'''