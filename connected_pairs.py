#===============================================================================

import logging
from pprint import pprint

import matplotlib.pyplot as plt
import networkx as nx
import requests

#===============================================================================

import nifstd_tools.simplify as nif

#===============================================================================

class Connectivity(object):
    ANNOTATES = 'apinatomy:annotates'
    CLONEOF = 'apinatomy:cloneOf'
    INTERNALIN = 'apinatomy:internalIn'
    LYPHS = 'apinatomy:lyphs'
    NEXT = 'apinatomy:next'
    NEXTS = 'apinatomy:next*'
    PUBLICATIONS = 'apinatomy:publications'

    def __init__(self, endpoint):
        self.__endpoint = endpoint
        self.__known_terms = set()

    @property
    def known_terms(self):
        return sorted(list(self.__known_terms))

    def query(self, neuron_population_id):
        url = f'{self.__endpoint}/dynamic/demos/apinat/neru-5/{neuron_population_id}.json?limit=9999999'
        response = requests.get(url, headers={'Accept': 'application/json'})
        return response.json()

    @staticmethod
    def isLayer(blob, s):
        return nif.ematch(blob, (lambda e, m: nif.sub(e, m) and nif.pred(e, nif.layerIn)), s)

    @staticmethod
    def reclr(blob, start_link):
        # recurse up the hierarchy until fasIn endIn intIn terminates
        collect = []
        layer = []
        col = True

        def select_ext(e, m, collect=collect):
            nonlocal col
            if nif.sub(e, m):
                if nif.pred(e, Connectivity.CLONEOF):  # should be zapped during simplify
                    return nif.ematch(blob, select_ext, nif.obj(e))
                if (nif.pred(e, nif.ext)
                 or nif.pred(e, nif.ie)
                 or nif.pred(e, nif.ies)):
                    external = nif.obj(e)
                    if col:
                        if layer:
                            l = layer.pop()
                        else:
                            l = None
                        r = [b for b in blob['nodes'] if b['id'] == external][0]['id']  # if this is empty we are in big trouble
                        collect.append((l, r))
                    else:
                        l = [b for b in blob['nodes'] if b['id'] == external][0]['id']
                        layer.append(l)
                    return external

        def select(e, m):
            nonlocal col
            if nif.sub(e, m):
                if (nif.pred(e, nif.layerIn)
                 or nif.pred(e, nif.fasIn)
                 or nif.pred(e, nif.endIn)
                 or nif.pred(e, Connectivity.INTERNALIN)):
                    col = not Connectivity.isLayer(blob, nif.obj(e))
                    nif.ematch(blob, select_ext, nif.obj(e))
                    nif.ematch(blob, select, nif.obj(e))

        nif.ematch(blob, select, start_link)

        return collect

    @staticmethod
    def layer_regions(blob, start):
        direct = [nif.obj(t) for t in
                  nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                    and (nif.pred(e, Connectivity.INTERNALIN)
                                      or nif.pred(e, nif.endIn)
                                      or nif.pred(e, nif.fasIn))),
                             start)]
        layers = [nif.obj(t) for d in direct for t in
                  nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                    and Connectivity.isLayer(blob, m)
                                    and (nif.pred(e, nif.ie)
                                      or nif.pred(e, nif.ies)
                                      or nif.pred(e, nif.ext))),
                             d)]
        lregs = []
        if layers:
            ldir = [nif.obj(t) for d in direct for t in
                    nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                      and nif.pred(e, nif.layerIn)),
                               d)]
            lregs = [nif.obj(t) for d in ldir for t in
                     nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                       and not Connectivity.isLayer(blob, m)
                                       and (nif.pred(e, nif.ie)
                                         or nif.pred(e, nif.ext))),
                                d)]
        regions = [nif.obj(t) for d in direct for t in
                   nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                     and not Connectivity.isLayer(blob, m)
                                     and (nif.pred(e, nif.ie)
                                       or nif.pred(e, nif.ies)
                                       or nif.pred(e, nif.ext))),
                              d)]

        lrs = Connectivity.reclr(blob, start)

        assert not (lregs and regions), (lregs, regions)  # not both
        regions = lregs if lregs else regions
        return start, tuple(lrs)

    def connectivity(self, neuron_population_id):
        blob_raw = self.query(neuron_population_id)
        blob, *_ = nif.apinat_deblob(blob_raw)
        starts = [nif.obj(e) for e in blob['edges'] if nif.pred(e, Connectivity.LYPHS)]
        nexts = [(nif.sub(t), nif.obj(t)) for start in starts for t in
                  nif.ematch(blob, (lambda e, m: nif.pred(e, Connectivity.NEXT)
                                              or nif.pred(e, Connectivity.NEXTS)), None)]

        #indexed = []
        #for n, p in enumerate(nexts):
        #    for m, e in enumerate(p):
        #        indexed.append(self.layer_regions(e, blob) + (m, ))
        #print('Indexed:')
        #pprint(sorted(set(indexed)))

        connected_pairs = sorted(set([tuple([self.layer_regions(blob, e) for e in p]) for p in nexts]))
        #print('Connected pairs:')
        #pprint(connected_pairs)

        return connected_pairs

    def node_id(self, connected_node):
        names = []
        for term in connected_node[1:]:
            if term is not None:
                self.__known_terms.add(term)
            names.append(str(term))
        return '\n'.join(names)

    def connectivity_graph(self, neuron_population_id, pdf=True, text=False):
        pairs = self.connectivity(neuron_population_id)
        G = nx.DiGraph()
        if text:
            print(neuron_population_id)
        n = 0
        for pair in pairs:
            nodes = (self.node_id(pair[0]), self.node_id(pair[1]))
#            print(f'    {pair[0]}  --->  {pair[1]}')
            if (nodes[0] != nodes[1]):
                G.add_edge(*nodes, directed=True, id=n)
                n += 1
#        print('Edges:')
        for edge in G.edges:
            node0 = edge[0].replace('\n', ', ')
            node1 = edge[1].replace('\n', ', ')
            if text:
                print(f'    ({node0})  --->  ({node1})')
        if text:
            print('')

        if (pdf):
            plt.figure()
            nx.draw(G, with_labels=True, node_color='#80F0F0', font_size=6)
            #nx.draw_spring(G, with_labels=True, node_color='#80F0F0', font_size=6)
            pdf_file = f"{neuron_population_id.split(':')[-1]}.pdf"
            if not text:
                print(f'Saving {neuron_population_id} to {pdf_file}')
            plt.savefig(pdf_file)
        return G

#===============================================================================

if __name__ == '__main__':

    connectivity = Connectivity('http://sparc-data.scicrunch.io:9000/scigraph')
    nodes = set()
    for pop_id in range(7, 8):
        G = connectivity.connectivity_graph(f'ilxtr:neuron-type-keast-{pop_id}', pdf=False, text=False)
        nodes.update(set(G.nodes))
    for node in sorted(nodes):
        n = node.replace('\n', ', ')
        print(f"({n})")
    """
    logging.basicConfig(level=logging.ERROR)

    knowledgestore = KnowledgeStore('.')
    for term in connectivity.known_terms:
        knowledge = knowledgestore.entity_knowledge(term)
        label = knowledge.get('label')
        if label == term: label = '** UNKNOWN **'
        print(f'{term}\t{label}')
    """

#===============================================================================
