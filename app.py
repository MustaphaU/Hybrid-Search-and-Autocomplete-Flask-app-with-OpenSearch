import re
from flask import Flask, render_template, request
from search import Search

app = Flask(__name__)
ops = Search()

@app.get('/')
def index():
    return render_template('index.html')

def extract_filters(query):
    filters= []

    category_regex = r'category:([^\s]+)\s*'
    matches = re.search(category_regex, query)
    if matches:
        filters.append({
            'term': {
                'category.keyword': {
                    'value': matches.group(1)
                }
            }
        })

        #remove the category filter from the query
        query = re.sub(category_regex, '', query).strip()

    #year filter
    year_regex = r'year:([^\s]+)\s*'
    matches = re.search(year_regex, query)
    if matches:
        filters.append({
            'range': {
                'updated_at': {
                    'gte': f'{matches.group(1)}||/y',
                    'lte': f'{matches.group(1)}||/y',
                }
            },
        })
        #remove the year filter from the query
        query = re.sub(year_regex, '', query).strip()

    return {'filter': filters}, query

@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    filters, parsed_query = extract_filters(query)
    from_ = request.form.get('from_', type=int, default=0)

    results = ops.search(
        query={
            "neural": {
                "summary_embedding": {
                    "query_text": parsed_query,
                    "model_id": ops.get_model_id("huggingface/sentence-transformers/all-MiniLM-L6-v2"),
                    "k": 5
                }
            }
        },
        size= 5,
        from_= from_,
    )
    
    return render_template('index.html', 
                        results=results['hits']['hits'], 
                        query=query, from_=from_, 
                        total=results['hits']['total']['value']
                        )
    # if parsed_query:
    #     search_query = {
    #         'must': {
    #             'multi_match': {
    #                 'query': parsed_query,
    #                 'fields': ['name', 'summary', 'content']
    #             }
    #         }
    #     }
    # else:
    #     search_query = {
    #         'must': {
    #             'match_all': {}
    #         }
    #     }
    # results = ops.search(
    #     query={
    #         'bool': {
    #             **search_query,
    #             **filters
    #         }
    #     },
    #     aggs={
    #         'category-agg': {
    #             'terms': {
    #                 'field': 'category.keyword',
    #             }
    #         },
    #         'year-agg': {
    #             'date_histogram': {
    #                 'field': 'updated_at',
    #                 'calendar_interval': 'year',
    #                 'format': 'yyyy',
    #             },
    #         },
    #     },
    #     size=5,
    #     from_=from_
    # )
    # aggs={
    #     'Category': {
    #         bucket['key']: bucket['doc_count']
    #         for bucket in results['aggregations']['category-agg']['buckets']
    #     },
    #     'Year': {
    #         bucket['key_as_string']: bucket['doc_count']
    #         for bucket in results['aggregations']['year-agg']['buckets']
    #         if bucket['doc_count'] > 0
    #     },
    # }
    # return render_template('index.html', 
    #                        results=results['hits']['hits'], 
    #                        query=query, from_=from_, 
    #                        total=results['hits']['total']['value'],
    #                        aggs=aggs)

@app.get('/document/<id>')
def get_document(id):
    document = ops.retrieve_document(id)
    title = document['_source']['name']
    paragraphs = document['_source']['content'].split('\n')
    return render_template('document.html', title=title, paragraphs=paragraphs)

@app.cli.command()
def reindex():
    """Regenerate the Opensearch index"""
    response = ops.reindex()
    print(f'Index with {len(response["items"])} documents created '
          f'in {response["took"]} milliseconds')