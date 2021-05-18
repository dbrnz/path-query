#===============================================================================

import json

#===============================================================================

import rdflib
import requests

from rdflib.namespace import RDF

#===============================================================================

SOMA_PROCESSES_URL = 'http://sparc-data.scicrunch.io:9000/scigraph/dynamic/demos/apinat/soma-processes.json'

#===============================================================================

APINATOMY_MODEL    = 'https://apinatomy.org/uris/models/{}'
APINATOMY_MODEL_ID = 'https://apinatomy.org/uris/models/{}/ids/{}'

#===============================================================================

namespaces = {
    'EMAPA': rdflib.namespace.Namespace('http://purl.obolibrary.org/obo/EMAPA_'),
    'FMA': rdflib.namespace.Namespace('http://purl.org/sig/ont/fma/fma'),
    'ILX': rdflib.namespace.Namespace('http://uri.interlex.org/base/ilx_'),
    'NCBITaxon': rdflib.namespace.Namespace('http://purl.obolibrary.org/obo/NCBITaxon_'),
    'NLX': rdflib.namespace.Namespace('http://uri.neuinfo.org/nif/nifstd/nlx_'),
    'RO': rdflib.namespace.Namespace('http://purl.obolibrary.org/obo/RO_'),
    'UBERON': rdflib.namespace.Namespace('http://purl.obolibrary.org/obo/UBERON_'),
    'apinatomy': rdflib.namespace.Namespace('https://apinatomy.org/uris/readable/'),
    'fma': rdflib.namespace.Namespace('http://purl.org/sig/ont/fma/'),
    'ilx': rdflib.namespace.Namespace('http://uri.interlex.org/'),
    'obo': rdflib.namespace.Namespace('http://purl.obolibrary.org/obo/'),
    }

#===============================================================================

def make_uri(name):
    if name.startswith('http:') or name.startswith('https:'):
        return rdflib.URIRef(name)
    elif ':' in name:
        (prefix, local) = name.split(':', 1)
        if prefix in namespaces:
            return namespaces[prefix][local]
        else:
            print('Unknown prefix:', name)
            return rdflib.URIRef(name)
    else:
        return rdflib.Literal(name)


#===============================================================================

APINATOMY_LINK = make_uri('apinatomy:Link')

PREDICATES_IGNORED = [
    'apinatomy:rootOf',
    'apinatomy:sourceOf',
]

#===============================================================================

def get_json(url):
    response = requests.get(url)
    return response.json()

#===============================================================================

def get_rdf_graph(model, neurons, query_data):
    model_uri = APINATOMY_MODEL.format(model)

    graph = rdflib.Graph()
    for pfx, ns in namespaces.items():
        graph.bind(pfx, ns, override=True)

    model_edges = [ edge for edge in query_data.get('edges', [])
                if 'Annotation' in edge.get('meta', {}).get('owlType', [])
                and model_uri in edge.get('meta', {}).get('isDefinedBy', []) ]

    # Have a list of neurons we are interested in
    # First go through edges building list of nodes connected to these neurons

    if len(neurons) == 0:
        connected_nodes = None
    else:
        connected_nodes = [APINATOMY_MODEL_ID.format(model, neuron) for neuron in neurons]
        grown = True
        while grown:
            grown = False
            for edge in model_edges:
                if edge['sub'] in connected_nodes and edge['obj'] not in connected_nodes:
                    connected_nodes.append(edge['obj'])
                    grown = True

    for edge in model_edges:
        if connected_nodes is None or edge['sub'] in connected_nodes:
            graph.add( (make_uri(edge['sub']), make_uri(edge['pred']), make_uri(edge['obj'])) )

    return graph

#===============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Save RDF about an ApiNATOMY model as Turtle.')
    parser.add_argument('--model', required=True,
                        help='name of an ApiNATOMY model, e.g. ``keast-bladder``')
    parser.add_argument('--neurons', nargs="+", default=[],
                        help='restrict to specific neurons, e.g. ``snl59 snl69``')
    parser.add_argument('--source', metavar='JSON',
                        help='JSON file resulting from a SciCrunch query')
    args = parser.parse_args()

    if args.source is not None:
        with open(args.source) as f:
            process_model = json.loads(f.read())
    else:
        process_model = get_json(SOMA_PROCESSES_URL)

    rdf = get_rdf_graph(args.model, args.neurons, process_model)
    model_uri = APINATOMY_MODEL.format(args.model)
    with open('{}.ttl'.format(args.model) if len(args.neurons) == 0
         else '{}_{}.ttl'.format(args.model, '_'.join(args.neurons)), 'w') as o:
        o.write(rdf.serialize(format='turtle', base=rdflib.URIRef(model_uri)).decode('utf-8'))

#===============================================================================
