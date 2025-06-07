import json
from pprint import pprint
import os
import time

from dotenv import load_dotenv
from opensearchpy import OpenSearch

load_dotenv()


class Search:
    def __init__(self):
        self.ops = OpenSearch(
            hosts = [{'host': 'localhost', 'port': 19200}],
            http_compress = True, # enables gzip compression for request bodies
            http_auth = (os.getenv("OPENSEARCH_ADMIN_USER"), os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD")),
            use_ssl = True,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn = False,

        )
        client_info = self.ops.info()
        print('Connected to Opensearch!')
        pprint(client_info)

    def create_index(self):
        self.ops.indices.delete(index='my_documents', ignore_unavailable=True)
        self.ops.indices.create(index='my_documents')

    def insert_document(self, document):
        return self.ops.index(index='my_documents', body=document)
    
    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append(document)
        return self.ops.bulk(body=operations)
    
    def reindex(self):
        self.create_index()
        with open('data.json','rt') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)
    
    def search(self, **query_args):
        body = query_args.get('query', {})
        print(f'Searching with query: {body}')
        return self.ops.search(index='my_documents', body={'query': body})