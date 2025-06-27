# OpenSearch Flask app for Hybrid Search (lexical and semantic) and Autocomplete.

## Demo
Click the play button in the top right corner of the GIF to view the demo.

[![Demo GIF](Demo/demo.gif)](Demo/demo.gif)

## Description
This project is a hybrid search Flask application that integrates traditional full-text (lexical/BM25) search with semantic (neural sparse embeddings) search. It also provides autocomplete functionality for an improved search experience.

### Inspiration:  
1. The project is an adaptation/extension of the [Elastic Search app](https://github.com/elastic/elasticsearch-labs/tree/main/example-apps/search-tutorial/v3/search-tutorial) in elasticsearch-labs.
2. The autocomplete query is a match_bool_prefix across multiple fields (with a disjunction maximum). It was adapted from the search service implementation in the [Amazon retail-demo-store project](https://github.com/aws-samples/retail-demo-store/blob/master/src/search/src/search-service/app.py).

#### *The primary adjustments to the* [Elastic Search app](https://github.com/elastic/elasticsearch-labs/tree/main/example-apps/search-tutorial/v3/search-tutorial) *are:*
1. OpenSearch is used as the search engine instead of Elasticsearch
2. A Neural Sparse Encoder, specifically [opensearch-neural-sparse-encoding-v2-distill](https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-v2-distill) is replaces Elasticsearch's [Elastic Learned Sparse EncodeR model (ELSER)](https://www.elastic.co/docs/solutions/search/semantic-search/semantic-search-elser-ingest-pipelines#:~:text=Elastic%20Learned%20Sparse%20EncodeR%20%2D%20or%20ELSER%20%2D%20is%20an%20NLP%20model%20trained%20by%20Elastic%20that%20enables%20you%20to%20perform%20semantic%20search%20by%20using%20sparse%20vector%20representation).
3. Autocomplete has been added.
4. The search box persists across the pages.


## Primary tools:
* OpenSearch
* Docker
* Flask

## Usage Instructions

### Start OpenSearch cluster locally in Docker
1. Start your Docker app or ensure it's running.
2. Clone the project and navigate to the project's root directory.
    ```bash
    git clone https://github.com/MustaphaU/opensearch-hybrid-search.git && cd opensearch-hybrid-search
    ```
3. Set the *`OPENSEARCH_INITIAL_ADMIN_PASSWORD`* to a strong password.   
    * Replace `{yourStrongPassword123!}` with your intended password and run the resulting command in your terminal.  
    * A valid password must contain a mix of upper and lower case alphanumeric characters and a special character. For example, `Myadminp@ss12321`  
    ```bash
    export OPENSEARCH_INITIAL_ADMIN_PASSWORD={yourStrongPassword123!}
    ```
4. Run docker-compose to start OpenSearch in Docker (in detached mode).
        ```bash
        docker compose up -d
        ```
    This command launches the services defined in [docker-compose.yaml](docker-compose.yml) in detached mode. It will:

    - Pull the latest `opensearch` and `opensearch-dashboards` images.
    - Start three containers:
      - Two OpenSearch cluster nodes: `opensearch-node1` and `opensearch-node2`
      - One dashboard instance: `opensearch-dashboards`
    - Automatically use the `OPENSEARCH_INITIAL_ADMIN_PASSWORD` from your environment for secure setup.

    Once the containers are running, OpenSearch and its dashboard will be available for use.

5. After the containers have started, access the OpenSearch Dashboards UI by navigating to the following URL in your browser:

    ```
    http://localhost:5002/
    ```

    When prompted, log in with:
    - **Username:** `admin`
    - **Password:** The value you set for `OPENSEARCH_INITIAL_ADMIN_PASSWORD`

### Setup and start the Search app
1. Create a **.env** file in the project's root directory and add your *`OPENSEARCH_INITIAL_ADMIN_PASSWORD`*:  

    `opensearch-hybrid-search/.env`

    ```bash
    OPENSEARCH_INITIAL_ADMIN_PASSWORD={yourStrongPassword123!}
    ```
2. Create and activate a conda environment (auto-accepting all prompts):
    ```bash
    conda create -y -n opensearch_env python=3.12
    conda activate opensearch_env
    ```

3. Install all requirements.
    ```bash
    pip install -r requirements.txt
    ```

4. Run below command to: 
   * Update cluster settings for model management  
   * Register and the deploy models  
   * Create ingest and hybrid search pipelines
   * Create index and ingest the data
    ```bash
    flask update-cluster-settings && flask deploy-models && flask create-pipelines && flask reindex
    ```
5. Start the search app
    ```bash
    flask run
    ```