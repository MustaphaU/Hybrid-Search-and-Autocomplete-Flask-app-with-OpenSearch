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
4. The search box persists across across all pages.



## Usage
1. Start by cloning the project
```bash
git clone 
```


