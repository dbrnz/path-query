#===============================================================================

import requests

#===============================================================================

#SCICRUNCH_QUERY_ENDPOINT = 'https://scicrunch.org/api/1/scigraph/cypher/execute'
SCICRUNCH_QUERY_ENDPOINT = 'http://sparc-data.scicrunch.io:9000/scigraph/cypher/execute'

API_KEY = 'xBOrIfnZTvJQtobGo8XHRvThdMYGTxtf'

#===============================================================================

MATCH_ALL = 'MATCH (n) RETURN n'


SPECIES_QUERY = """MATCH (n)
      WHERE n.iri IN [
              "http://purl.obolibrary.org/obo/NCBITaxon_9378",   // Suncus murinus
              "http://purl.obolibrary.org/obo/NCBITaxon_9606",   // Homo sapiens
              "http://purl.obolibrary.org/obo/NCBITaxon_9685",   // Felis catus
              "http://purl.obolibrary.org/obo/NCBITaxon_9823",   // Sus scrofa
              "http://purl.obolibrary.org/obo/NCBITaxon_10090",  // Mus musculus
              "http://purl.obolibrary.org/obo/NCBITaxon_10116"   // Rattus norvegicus
              ]
      RETURN n"""


SOMAS_QUERY = """MATCH (c:Class{iri: "http://uri.neuinfo.org/nif/nifstd/nlx_154731"})
      -[:apinatomy:annotates]->(soma:NamedIndividual)
      RETURN soma"""


SOMA_PROCESSES_QUERY = """MATCH path1 = (c:Class{iri: "http://uri.neuinfo.org/nif/nifstd/nlx_154731"})
      -[:apinatomy:annotates]->(soma:NamedIndividual)    // soma lyph
      -[:apinatomy:conveys]->(linkSoma)                  // link connecting soma to axon and dendrite
      -[:apinatomy:target|apinatomy:source]->(nodeRoot)  // axon or dendrite root
      -[:apinatomy:sourceOf|apinatomy:nextChainStartLevels|apinatomy:next*1..]->(link)  // sourceOf is first and only once
      -[:apinatomy:fasciculatesIn]->(layer_or_end)
      -[:apinatomy:cloneOf*0..1]->()
      -[:apinatomy:supertype*0..1]->()
      -[:apinatomy:external]->(external)
      WHERE soma.`https://apinatomy.org/uris/readable/generated` IS NULL
      WITH path1, nodeRoot, layer_or_end AS layer
      OPTIONAL MATCH path2 = (layer)  // if we were in a layer, get the containing lyph as well
      -[:apinatomy:layerIn]->(end_housing)
      -[:apinatomy:external]->(end_housing_external)
      WITH path1, path2, nodeRoot
      MATCH path3 = (nodeRoot)        // extract chain for axon vs dendrite
      -[:apinatomy:rootOf]->(chain)
      RETURN path1, path2, path3"""


TEST_QUERY_1 = """MATCH path1 = (c:Class{iri: "http://uri.neuinfo.org/nif/nifstd/nlx_154731"})
      -[:apinatomy:annotates]->(soma:NamedIndividual)    // soma lyph
      -[:apinatomy:conveys]->(linkSoma)                  // link connecting soma to axon and dendrite
      -[:apinatomy:target|apinatomy:source]->(nodeRoot)  // axon or dendrite root
      -[:apinatomy:sourceOf|apinatomy:nextChainStartLevels|apinatomy:next*1..]->(link)  // sourceOf is first and only once
      -[:apinatomy:fasciculatesIn]->(layer_or_end)
      -[:apinatomy:cloneOf*0..1]->()
      -[:apinatomy:supertype*0..1]->()
      -[:apinatomy:external]->(external)
      WHERE soma.`https://apinatomy.org/uris/readable/generated` IS NULL
      WITH path1, nodeRoot, layer_or_end AS layer
      OPTIONAL MATCH path2 = (layer)  // if we were in a layer, get the containing lyph as well
      -[:apinatomy:layerIn]->(end_housing)
      -[:apinatomy:external]->(end_housing_external)
      WITH path1, path2, nodeRoot
      MATCH path3 = (nodeRoot)        // extract chain for axon vs dendrite
      -[:apinatomy:rootOf]->(chain)
      RETURN path1, path2, path3"""

TEST_QUERY_2 = """MATCH path1 = (c:Class{iri: "http://uri.neuinfo.org/nif/nifstd/nlx_154731"})
      -[:https://apinatomy.org/uris/readable/annotates]->(soma:NamedIndividual)    // soma lyph
      -[:https://apinatomy.org/uris/readable/conveys]->(linkSoma)                  // link connecting soma to axon and dendrite
      -[:https://apinatomy.org/uris/readable/target|https://apinatomy.org/uris/readable/source]->(nodeRoot)  // axon or dendrite root
      -[:https://apinatomy.org/uris/readable/sourceOf|https://apinatomy.org/uris/readable/nextChainStartLevels|https://apinatomy.org/uris/readable/next*1..]->(link)  // sourceOf is first and only once
      -[:https://apinatomy.org/uris/readable/fasciculatesIn]->(layer_or_end)
      -[:https://apinatomy.org/uris/readable/cloneOf*0..1]->()
      -[:https://apinatomy.org/uris/readable/supertype*0..1]->()
      -[:https://apinatomy.org/uris/readable/external]->(external)
      WHERE soma.`https://apinatomy.org/uris/readable/generated` IS NULL
      WITH path1, nodeRoot, layer_or_end AS layer
      OPTIONAL MATCH path2 = (layer)  // if we were in a layer, get the containing lyph as well
      WITH path1, path2, nodeRoot
      RETURN path1, path2"""


#===============================================================================

def query(cypher, limit=10):
    response = requests.get(
        SCICRUNCH_QUERY_ENDPOINT,
        headers={
            'accept': 'application/json'
        },
        params={
            'api_key': API_KEY,
            'cypherQuery': cypher,
            'limit': limit
        })
    #print(response.headers)
    response.raise_for_status()
    return response.text

#===============================================================================

#print(query(SPECIES_QUERY))
print(query(SOMAS_QUERY))

#===============================================================================
