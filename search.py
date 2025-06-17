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

    # update cluster settings to enable model
    def update_cluster_settings(self):
        self.ops.cluster.put_settings(
            body={
                "persistent": {
                    "plugins.ml_commons.only_run_on_ml_node": False,
                    "plugins.ml_commons.model_access_control_enabled": True,
                    "plugins.ml_commons.native_memory_threshold": "99",
                    "plugins.ml_commons.model_auto_redeploy.enable": True,
                    "plugins.ml_commons.model_auto_redeploy.lifetime_retry_times": 3,
                }
            }
        )
        print("Cluster settings updated to enable model management.")

    # register model group
    def register_model_group(
        self,
        name="Model_Group",
        description="Public ML Model Group",
        access_mode="public",
    ):
        # Check if model group already exists
        existing_groups = self.ops.transport.perform_request(
            "GET",
            "/_plugins/_ml/model_groups/_search",
            body={
                "query": {"term": {"name.keyword": name}},
                "_source": ["model_group_id"],
                "size": 1,
            },
        )
        if existing_groups["hits"]["hits"]:
            model_group_id = existing_groups["hits"]["hits"][0]["_id"]
            print(f"Model group '{name}' already exists with ID: {model_group_id}")
            return model_group_id
        else:
            print(f"Registering new model group '{name}'...")
            response = self.ops.transport.perform_request(
                "POST",
                "/_plugins/_ml/model_groups/_register",
                body={
                    "name": name,
                    "description": description,
                    "access_mode": access_mode,
                },
            )
            print(f"Model group '{name}' registered.")
            model_group_id = response["model_group_id"]
            print(f"Model group ID: {model_group_id}")
            return model_group_id  # to be changed later

    def get_model_id(self, model_name):
        models = self.ops.transport.perform_request(
            "GET",
            "/_plugins/_ml/models/_search",
            body={
                "query": {"term": {"name.keyword": model_name}},
                "_source": ["model_id"],
                "size": 1,
            },
        )

        if models["hits"]["hits"]:
            return models["hits"]["hits"][0]["_source"]["model_id"]
        else:
            raise ValueError(f"{model_name} model not found.")

    # deploy "huggingface/sentence-transformers/all-MiniLM-L6-v2" and "amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill"
    def deploy_models(self):
        model_group_id = self.register_model_group()
        print(f"Model group ID: {model_group_id}")
        sparse_model_name = (
            "amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill"
        )
        dense_model_name = "huggingface/sentence-transformers/all-MiniLM-L6-v2"
        model_names = [sparse_model_name, dense_model_name]
        model_configs = {sparse_model_name: "1.0.0", dense_model_name: "1.0.2"}
        sparse_model_id = None
        dense_model_id = None
        try:
            sparse_model_id = self.get_model_id(sparse_model_name)
            print(f"Sparse model ID: {sparse_model_id}")
            dense_model_id = self.get_model_id(dense_model_name)
            print(f"Dense model ID: {dense_model_id}")
            # check if models are already deployed
            sparse_model_is_deployed = (self.ops.transport.perform_request("GET", f"/_plugins/_ml/models/{sparse_model_id}").get("model_state")== "DEPLOYED")
            print(f"Sparse model is deployed: {sparse_model_is_deployed}")
            dense_model_is_deployed = (self.ops.transport.perform_request("GET", f"/_plugins/_ml/models/{dense_model_id}").get("model_state")== "DEPLOYED")
            print(f"Dense model is deployed: {dense_model_is_deployed}")
            if sparse_model_is_deployed and dense_model_is_deployed:
                print("Models are already deployed.")
                return
            else:
                #error out so that we can move to the except block
                raise Exception("Models are not deployed.")
        except Exception as exc:
            print(exc)
            # delete models if they exist and IDs are available
            if sparse_model_id:
                # undeploy the model first
                self.ops.transport.perform_request(
                    "POST", f"/_plugins/_ml/models/{sparse_model_id}/_undeploy"
                )
                print(f"Model '{sparse_model_name}' undeployed successfully.")
                self.ops.transport.perform_request(
                    "DELETE", f"/_plugins/_ml/models/{sparse_model_id}"
                )
            if dense_model_id:
                # undeploy the model first
                self.ops.transport.perform_request(
                    "POST", f"/_plugins/_ml/models/{dense_model_id}/_undeploy"
                )
                print(f"Model '{dense_model_name}' undeployed successfully.")
                self.ops.transport.perform_request(
                    "DELETE", f"/_plugins/_ml/models/{dense_model_id}"
                )
            print("registering and deploying models...")
            for model_name in model_names:
                response = self.ops.transport.perform_request(
                    "POST",
                    "/_plugins/_ml/models/_register",
                    body={
                        "name": model_name,
                        "version": model_configs[model_name],
                        "model_group_id": model_group_id,
                        "model_format": "TORCH_SCRIPT",
                    },
                )
                task_id = response["task_id"]
                print(
                    f"task id: {task_id} for model '{model_name}' registration received."
                )
                # wait for the model to be registered
                task_status = None
                while task_status not in ["COMPLETED", "FAILED"]:
                    print(
                        f"Waiting for model '{model_name}' registration to complete..."
                    )
                    response = self.ops.transport.perform_request(
                        "GET", f"/_plugins/_ml/tasks/{task_id}"
                    )
                    task_status = response["state"]
                    print(f"Current task status: {task_status}")
                    time.sleep(15)
                if task_status == "COMPLETED":
                    print(f"Model '{model_name}' registered successfully.")
                    model_id = response["model_id"]
                    # deploy the model
                    deploy_response = self.ops.transport.perform_request(
                        "POST", f"/_plugins/_ml/models/{model_id}/_deploy"
                    )
                    deploy_task_id = deploy_response["task_id"]
                    print(
                        f"task id: {deploy_task_id} for model '{model_name}' deployment received."
                    )
                    # wait for the model to be deployed
                    deploy_task_status = None
                    while deploy_task_status not in ["COMPLETED", "FAILED"]:
                        print(
                            f"Waiting for model '{model_name}' deployment to complete..."
                        )
                        deploy_task_status = self.ops.transport.perform_request(
                            "GET", f"/_plugins/_ml/tasks/{deploy_task_id}"
                        )["state"]
                        print(f"Current task status: {deploy_task_status}")
                        time.sleep(15)
                    if deploy_task_status == "COMPLETED":
                        print(f"Model '{model_name}' deployed successfully.")
                    else:
                        print(
                            f"Model '{model_name}' deployment failed. Task status is {deploy_task_status}"
                        )
                elif task_status == "FAILED":
                    print(
                        f"Model '{model_name}' registration failed. Task status is {task_status}"
                    )
                else:
                    print(
                        f"Model '{model_name}' registration failed. Task status is {task_status}"
                    )

    def create_pipelines(self):
        self.ops.ingest.put_pipeline(
            id="hybrid-ingest-pipeline",
            body={
                "description": "A pipeline of dense and sparse processors",
                "processors": [
                    {
                        "sparse_encoding": {
                            "model_id": self.get_model_id("amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill"),
                            "field_map": {"summary": "summary_sparse_embedding"},
                        }
                    },
                    {
                        "text_embedding": {
                            "model_id": self.get_model_id("huggingface/sentence-transformers/all-MiniLM-L6-v2"),
                            "field_map": {"summary": "summary_dense_embedding"},
                        }
                    },
                ],
            },
        )
        print(
            "Hybrid ingest pipeline created with dense and sparse embedding processors."
        )
        #rrf pipeline
        self.ops.transport.perform_request(
            "PUT",
            "/_search/pipeline/rrf-pipeline",
            body={
                "description": "Post processor for hybrid RRF search",
                "phase_results_processors": [
                    {
                        "score-ranker-processor": {
                            "combination": {
                                "technique": "rrf"
                            }
                        }
                    }
                ],
            },
        )
        print("RRF search pipeline created.")

    def create_index(self):
        self.ops.indices.delete(index="my_documents", ignore_unavailable=True)
        self.ops.indices.create(
            index="my_documents",
            body={
                "settings": {
                    "index.knn": True,
                    "default_pipeline": "hybrid-ingest-pipeline",
                },
                "mappings": {
                    "properties": {
                        "summary_dense_embedding": {
                            "type": "knn_vector",
                            "dimension": 384,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "lucene",
                            },
                        },
                        "summary_sparse_embedding": {
                            "type": "rank_features",
                        },
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
        print(f"query args: {query_args}")
        return self.ops.search(
            index="my_documents",
            body=query_args,
            params={"search_pipeline": "rrf-pipeline"},
        )

    def retrieve_document(self, id):
        return self.ops.get(index="my_documents", id=id)