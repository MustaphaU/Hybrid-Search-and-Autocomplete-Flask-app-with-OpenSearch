# Lexical (BM25) and Neural (Sparse Embeddings) Hybrid Search with Autocomplete Using OpenSearch

## Description
This project demonstrates a hybrid search application that combines traditional full-text (lexical/BM25) search with semantic (neural) search using sparse embeddings powered by OpenSearch. It also provides autocomplete functionality for imrpoved user search experience.

### Inspiration:  
1. This work is an adaptation/extension of the [Elastic Search app](https://github.com/elastic/elasticsearch-labs/tree/main/example-apps/search-tutorial/v3/search-tutorial) in elasticsearch-labs.
2. The query for autocomplete and results post-processing is a match_bool_prefix across multiple fields (with a disjunction maximum). It was adapted from search service implementation in [Amazon retail-demo-store project](https://github.com/aws-samples/retail-demo-store/blob/master/src/search/src/search-service/app.py).

#### *The primary adjustments to the* [Elastic Search app](https://github.com/elastic/elasticsearch-labs/tree/main/example-apps/search-tutorial/v3/search-tutorial) *are:*
1. OpenSearch is used as the search engine instead of Elasticsearch
2. A Neural Sparse Encoder, specifically [opensearch-neural-sparse-encoding-v2-distill](https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-v2-distill) is used as replacement for Elasticsearch's [Elastic Learned Sparse EncodeR model (ELSER)](https://www.elastic.co/docs/solutions/search/semantic-search/semantic-search-elser-ingest-pipelines#:~:text=Elastic%20Learned%20Sparse%20EncodeR%20%2D%20or%20ELSER%20%2D%20is%20an%20NLP%20model%20trained%20by%20Elastic%20that%20enables%20you%20to%20perform%20semantic%20search%20by%20using%20sparse%20vector%20representation).
3. Autocompletion has been added.
4. The search box persists across all pages.



## Usage
1. Start your Docker app or ensure it's running.
2. Clone the project and navigate to the project's root directory.
    ```bash
    git clone https://github.com/MustaphaU/opensearch-hybrid-search.git && cd opensearch-hybrid-search
    ```
3. Create and activate a conda environment for Python 3.12 (auto-accepting all prompts):
    ```bash
    conda create -y -n opensearch_env python=3.12
    conda activate opensearch_env
    ```
4. Set the OPENSEARCH_INITIAL_ADMIN_PASSWORD to a strong password.   
    * Replace `{yourStrongPassword123!}` with your intended password and run the resulting command in your terminal.  
    * A valid password must contain a mix of upper and lower case alphanumeric characters and a special character. For example, `Myadminp@ss12321`  
    ```bash
    export OPENSEARCH_INITIAL_ADMIN_PASSWORD={yourStrongPassword123!}
    ```
5. Run docker-compose to start OpenSearch in docker (in detached mode).
    ```bash
    docker-compose up -d
    ```
    This executes the instructions in [docker-compose.yaml](docker-compose.yml). It primarily pulls the latest opensearch and opensearch-dashboards images, and starts three containers: two opensearch cluster nodes namely `opensearch-node1` and `opensearch-node2` and one opensearch-dashboard named `opensearch-dashboards`.
    The OPENSEARCH_INITIAL_ADMIN_PASSWORD will be programmatically fetched from your environment.

6. Once the containers successfully start, you can access your opensearch dashboard by opening the url in your browser. 
Once prompted, enter the default username `Admin` and your *`OPENSEARCH_INITIAL_ADMIN_PASSWORD`*.
    ```bash
    http://localhost:5002/
    ```










