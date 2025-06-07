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

        )  # <-- connection options need to be added here
        client_info = self.ops.info()
        print('Connected to Opensearch!')
        pprint(client_info)