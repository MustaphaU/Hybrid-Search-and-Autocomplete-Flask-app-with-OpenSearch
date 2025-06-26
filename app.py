import re
from flask import Flask, render_template, request, jsonify
from search import Search

app = Flask(__name__)
ops = Search()


@app.get("/")
def index():
    return render_template("index.html")


def extract_filters(query):
    filters = []

    category_regex = r"category:([^\s]+)\s*"  # matches like "category:books" because of the \s* at the end which allows for optional whitespace after the category
    matches = re.search(category_regex, query)
    if matches:
        filters.append({"term": {"category.keyword": {"value": matches.group(1)}}})

        # remove the category filter from the query
        query = re.sub(category_regex, "", query).strip()

    # year filter
    year_regex = r"year:([^\s]+)\s*"
    matches = re.search(year_regex, query)
    if matches:
        filters.append(
            {
                "range": {
                    "updated_at": {
                        "gte": f"{matches.group(1)}||/y",
                        "lte": f"{matches.group(1)}||/y",
                    }
                },
            }
        )
        # remove the year filter from the query
        query = re.sub(year_regex, "", query).strip()

    return {"filter": filters}, query


@app.post("/")
def handle_search():
    query = request.form.get("query", "")
    filters, parsed_query = extract_filters(query)
    from_ = request.form.get("from_", type=int, default=0)

    if parsed_query.strip():
        lex_query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": parsed_query,
                            "fields": ["name", "summary", "content"],
                        }
                    }
                ],
                **filters,
            }
        }
        # neural query setup with filters
        model_id = ops.get_model_id(
            "amazon/neural-sparse/opensearch-neural-sparse-encoding-v2-distill"
        )

        neural_query = {
            "bool": {
                "must": [
                    {
                        "neural_sparse": {
                            "summary_sparse_embedding": {
                                "query_text": parsed_query,
                                "model_id": model_id,
                            }
                        }
                    }
                ],
                **filters,
            }
        }
        # combine the lexical and neural queries in a hybrid query
        search_query = {
            "hybrid": {
                "queries": [
                    lex_query,
                    neural_query,
                ],
                "pagination_depth": 50,  #It specifies the maximum number of search results to retrieve from each shard for every subquery.
            }
        }
    else:
        search_query = {"bool": {"must": [{"match_all": {}}], **filters}}

    results = ops.search(
        query=search_query,
        aggs={
            "category-agg": {
                "terms": {
                    "field": "category.keyword",
                }
            },
            "year-agg": {
                "date_histogram": {
                    "field": "updated_at",
                    "calendar_interval": "year",
                    "format": "yyyy",
                },
            },
        },
        size=5,
        from_=from_,
    )

    # Process aggregations
    aggs = {
        "Category": {
            bucket["key"]: bucket["doc_count"]
            for bucket in results["aggregations"]["category-agg"]["buckets"]
        },
        "Year": {
            bucket["key_as_string"]: bucket["doc_count"]
            for bucket in results["aggregations"]["year-agg"]["buckets"]
            if bucket["doc_count"] > 0
        },
    }

    return render_template(
        "index.html",
        results=results["hits"]["hits"],
        query=query,
        from_=from_,
        total=results["hits"]["total"]["value"],
        aggs=aggs,
    )


# route for autocomplete suggestions
@app.route("/autocomplete", methods=["POST"])
def autocomplete():
    search_term = request.form.get("query", "")
    size = 10
    collapse_size = 5
    query_args = {
        "from": 0,
        "size": size,
        "query": {
            "dis_max": {
                "queries": [
                    {"match_bool_prefix": {"name": {"query": search_term, "boost": 1.2}}},
                    {"match_bool_prefix": {"category": {"query": search_term}}},
                    {"match_bool_prefix": {"summary": {"query": search_term}}},
                    {"match_bool_prefix": {"content": {"query": search_term, "boost": 0.5}}},
                ],
                "tie_breaker": 0.7,
            }
        },
        "fields": ["name", "category", "summary", "content"],
        "_source": False,
        "collapse": {
            "field": "category.keyword",
            "inner_hits": {
                "name": "category_hits",
                "size": collapse_size,
                "fields": ["name"],
                "_source": False,
            },
        },
    }

    results =ops.search(**query_args)

    # Post-process results to ensure diverse categories
    total_hits = results["hits"]["total"]["value"]
    cats_with_hits = len(results["hits"]["hits"])
    avg_hits_cat = int(size / cats_with_hits) if cats_with_hits > 0 else 0
    hits_for_cats = []
    accum_hits = 0
    cats_with_more = 0

    for item in results["hits"]["hits"]:
        cat_hits = item["inner_hits"]["category_hits"]["hits"]["total"]["value"]
        if cat_hits > avg_hits_cat:
            cats_with_more += 1
        hits_this_cat = min(cat_hits, avg_hits_cat)
        hits_for_cats.append([cat_hits, hits_this_cat])
    
    if accum_hits < size and cats_with_more:
        more_each = int((size - accum_hits) / cats_with_more)
        for counts in hits_for_cats:
            more_this_cat = min(more_each, counts[0] - counts[1])
            accum_hits += more_this_cat
            counts[1] += more_this_cat

    found_items = []

    for idx, item in enumerate(results["hits"]["hits"]):
        cat_hits = item["inner_hits"]["category_hits"]["hits"]["hits"]

        if accum_hits < size and hits_for_cats[idx][1] < hits_for_cats[idx][0]:
            to_add = min(size - accum_hits, hits_for_cats[idx][0] - hits_for_cats[idx][1])
            hits_for_cats[idx][1] += to_add
            accum_hits += to_add

        added = 0
        for hit in cat_hits:
            found_items.append({
                'itemId': hit['_id'],
                'name': hit['fields'].get('name', [None])[0],
                'category': item['fields'].get('category', [None])[0],
            })
            added += 1
            if added == hits_for_cats[idx][1]:
                break
    return jsonify(found_items)


@app.get("/document/<id>")
def get_document(id):
    document = ops.retrieve_document(id)
    title = document["_source"]["name"]
    paragraphs = document["_source"]["content"].split("\n")
    return render_template("document.html", title=title, paragraphs=paragraphs)


@app.cli.command()
def update_cluster_settings():
    """Update cluster settings to enable model management"""
    try:
        ops.update_cluster_settings()
    except Exception as exc:
        print(f"Error updating cluster settings: {exc}")


@app.cli.command()
def deploy_models():
    """Deploy models to the Opensearch cluster"""
    try:
        ops.deploy_models()
    except Exception as exc:
        print(f"Error deploying models: {exc}")


@app.cli.command()
def create_pipelines():
    """Create pipelines for the Opensearch cluster"""
    try:
        ops.create_pipelines()
    except Exception as exc:
        print(f"Error creating pipelines: {exc}")

@app.cli.command()
def reindex():
    """Regenerate the Opensearch index"""
    response = ops.reindex()
    print(
        f"Index with {len(response['items'])} documents created "
        f"in {response['took']} milliseconds"
    )