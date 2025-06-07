import re
from flask import Flask, render_template, request
from search import Search

app = Flask(__name__)
ops = Search()

@app.get('/')
def index():
    return render_template('index.html')


@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    results = ops.search(
        query={
            'match': {
                'name': {
                    'query': query
                }
            }
        }
    )
    return render_template('index.html', 
                           results=results['hits']['hits'], 
                           query=query, from_=0, 
                           total=results['hits']['total']['value'])



@app.get('/document/<id>')
def get_document(id):
    document = ops.retrieve_document(id)
    title = document['_source']['name']
    print(f'title: {title}')
    paragraphs = document['_source']['content'].split('\n')
    print(f'paragraphs: {paragraphs}')
    return render_template('document.html', title=title, paragraphs=paragraphs)

@app.cli.command()
def reindex():
    """Regenerate the Opensearch index"""
    response = ops.reindex()
    print(f'Index with {len(response["items"])} documents created '
          f'in {response["took"]} milliseconds')