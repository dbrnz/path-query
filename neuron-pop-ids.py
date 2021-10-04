#===============================================================================

import json

#===============================================================================

import requests

#===============================================================================

CYPHER_ENDPOINT = 'http://sparc-data.scicrunch.io:9000/scigraph/cypher/execute'

API_KEY = None   ##  'xBOrIfnZTvJQtobGo8XHRvThdMYGTxtf'

#===============================================================================

def cypher_query(cypher, format='json', limit=100):
    query_params = { 'cypherQuery': cypher }
    if limit is not None:
        query_params['limit'] = limit
    if API_KEY is not None:
        query_params['api_key'] = API_KEY
    response = requests.get(CYPHER_ENDPOINT,
        headers={
            'accept': 'application/json' if format=='json' else 'text/plain'
        },
        params=query_params)
    response.raise_for_status()
    return response.json() if format=='json' else response.text

#===============================================================================

QUERY_CONN_MODELS = 'MATCH ({iri: "https://apinatomy.org/uris/elements/Graph"})<-[:type]-(g)-[:isDefinedBy]->(o:Ontology) RETURN o'

QUERY_NEURON_IDS = """
    MATCH (start:Ontology {iri: $model_id})
        <-[:isDefinedBy]-(external:Class)
        -[:subClassOf*]->(:Class {iri: "http://uri.interlex.org/tgbugs/uris/readable/NeuronEBM"}) // FIXME
    WITH external
    MATCH (external)
        -[e:type]->()
    RETURN e
UNION
    MATCH (start:Ontology {iri: $model_id})
        <-[:isDefinedBy]-(graph:NamedIndividual)
        -[:type]->({iri: "https://apinatomy.org/uris/elements/Graph"}) // elements don't have a superclass right now
    WITH graph
    MATCH (graph)
        -[:apinatomy:publications]->(pub)
        -[e:type]-()
    RETURN e
"""

#===============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Get neuron population ids for a connectivity model')
    parser.add_argument('--format', metavar='FORMAT',
        choices=['json', 'text'], default='json')
    parser.add_argument('--limit', metavar='LIMIT', type=int, default=10,
        help='The number of records to return')
    parser.add_argument('--model', metavar='MODEL',
        help='If no model given then return the available connectivity models')

    args = parser.parse_args()
    if args.model is None:
        query = QUERY_CONN_MODELS
    else:
        query = QUERY_NEURON_IDS.replace('$model_id', f'"{args.model}"')

    result = cypher_query(query, format=args.format, limit=args.limit)
    if args.format == 'json':
        print(json.dumps(result, indent=4))
    else:
        print(result)

#===============================================================================

if __name__ == '__main__':
    main()

#===============================================================================
