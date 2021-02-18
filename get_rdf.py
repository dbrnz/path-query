#===============================================================================

import json

#===============================================================================

import rdflib
import requests

#===============================================================================

SOMA_PROCESSES_URL = 'http://sparc-data.scicrunch.io:9000/scigraph/dynamic/demos/apinat/soma-processes.json'

#===============================================================================

APINATOMY_MODEL_BASE = 'https://apinatomy.org/uris/models/{}'

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

def get_json(url):
    response = requests.get(url)
    return response.json()

#===============================================================================

def get_rdf(model, query):
    model_uri = APINATOMY_MODEL_BASE.format(model)

    graph = rdflib.Graph()
    for pfx, ns in namespaces.items():
        graph.bind(pfx, ns, override=True)

    for edge in query.get('edges', []):
        meta = edge.get('meta', {})
        if ('Annotation' in meta.get('owlType', [])
        and model_uri in meta.get('isDefinedBy', [])):
            graph.add( (make_uri(edge['sub']), make_uri(edge['pred']), make_uri(edge['obj'])) )
    return graph

#===============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Extract RDF about an ApiNATOMY model.')
    parser.add_argument('--model', required=True,
                        help='name of ApiNATOMY model')
    parser.add_argument('--source', metavar='JSON',
                        help='JSON file resulting from a SciCrunch query')
    args = parser.parse_args()

    if args.source is not None:
        with open(args.source) as f:
            process_model = json.loads(f.read())
    else:
        process_model = get_json(SOMA_PROCESSES_URL)

    rdf = get_rdf(args.model, process_model)
    model_uri = APINATOMY_MODEL_BASE.format(args.model)
    with open('{}.ttl'.format(args.model), 'w') as o:
        o.write(rdf.serialize(format='turtle', base=rdflib.URIRef(model_uri)).decode('utf-8'))

        # Don't set `base=map_uri` until RDFLib 5.0 and then use `explicit_base=True`
        # See https://github.com/RDFLib/rdflib/issues/559

#===============================================================================
