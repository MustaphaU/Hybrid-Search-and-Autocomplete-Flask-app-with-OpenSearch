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
            hosts=[{"host": "localhost", "port": 19200}],
            http_compress=True,  # enables gzip compression for request bodies
            http_auth=(
                os.getenv("OPENSEARCH_ADMIN_USER"),
                os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD"),
            ),
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        client_info = self.ops.info()
        print("Connected to Opensearch!")
        pprint(client_info)

    def get_model_id(self, model_name):
        models = self.ops.transport.perform_request("GET", "/_plugins/_ml/models/_search", 
            body={
                "query": {
                    "term": {
                        "name.keyword": model_name
                    }
                },
                "_source": ["model_id"],
                "size": 1,
            }
        )

        if models["hits"]["hits"]:
            return models["hits"]["hits"][0]["_source"]["model_id"] 
        else:
            raise ValueError(f"{model_name} model not found.")

    def create_index(self):
        self.ops.indices.delete(index="my_documents", ignore_unavailable=True)
        self.ops.indices.create(
            index="my_documents",
            body={
                "settings": {
                    "index.knn": True,
                    "default_pipeline": "embedding-ingest-pipeline-l6mini",
                },
                "mappings": {
                    "properties": {
                        "summary_embedding": {
                            "type": "knn_vector",
                            "dimension": 384,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "lucene",
                            },
                        }
                    }
                },
            },
        )

    def insert_document(self, document):
        return self.ops.index(index="my_documents", body=document)

    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({"index": {"_index": "my_documents"}})
            operations.append(document)
        return self.ops.bulk(body=operations)

    def reindex(self):
        self.create_index()
        with open("data.json", "rt") as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)

    def search(self, **query_args):
        if "from_" in query_args:
            query_args["from"] = query_args["from_"]
            del query_args["from_"]
        return self.ops.search(index="my_documents", body=json.dumps(query_args))

    def retrieve_document(self, id):
        return self.ops.get(index="my_documents", id=id)
