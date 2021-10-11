#===============================================================================

from pprint import pprint

import matplotlib.pyplot as plt
import networkx as nx
import requests

#===============================================================================

import nifstd_tools.simplify as nif

#===============================================================================

class Connectivity(object):
    LYPHS = 'apinatomy:lyphs'
    NEXT = 'apinatomy:next'
    NEXTS = 'apinatomy:next*'
    INTERNALS = 'apinatomy:internalIn'

    def __init__(self, endpoint):
        self.__endpoint = endpoint

    def query(self, neuron_population_id):
        url = f'{self.__endpoint}/dynamic/demos/apinat/neru-4/{neuron_population_id}.json?limit=9999999'
        response = requests.get(url, headers={'Accept': 'application/json'})
        return response.json()

    @staticmethod
    def isLayer(s, blob):
        return nif.ematch(blob, (lambda e, m: nif.sub(e, m) and nif.pred(e, nif.layerIn)), s)

    @staticmethod
    def layer_regions(start, blob):
        direct = [nif.obj(t) for t in
                  nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                    and (nif.pred(e, Connectivity.INTERNALS) or
                                         nif.pred(e, nif.endIn) or
                                         nif.pred(e, nif.fasIn))),
                             start)]
        layers = [nif.obj(t) for d in direct for t in
                  nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                    and Connectivity.isLayer(m, blob)
                                    and (nif.pred(e, nif.ie) or
                                         nif.pred(e, nif.ext))),
                             d)]
        lregs = []
        if layers:
            ldir = [nif.obj(t) for d in direct for t in
                    nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                      and nif.pred(e, nif.layerIn)),
                               d)]
            lregs = [nif.obj(t) for d in ldir for t in
                     nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                       and not Connectivity.isLayer(m, blob)
                                       and (nif.pred(e, nif.ie) or
                                            nif.pred(e, nif.ext))),
                                d)]
        regions = [nif.obj(t) for d in direct for t in
                   nif.ematch(blob, (lambda e, m: nif.sub(e, m)
                                     and not Connectivity.isLayer(m, blob)
                                     and (nif.pred(e, nif.ie) or
                                          nif.pred(e, nif.ext))),
                              d)]
        assert not (lregs and regions), (lregs, regions)  # not both
        regions = lregs if lregs else regions
        return start, layers[0] if layers else None, regions[0] if regions else None


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

        connected_pairs = sorted(set([tuple([self.layer_regions(e, blob) for e in p]) for p in nexts]))
        #print('Connected pairs:')
        #pprint(connected_pairs)

        return connected_pairs

    @staticmethod
    def node_id(connected_node):
        return '\n'.join([str(k) for k in connected_node[1:]])

    def draw_connectivity_graph(self, neuron_population_id):
        pairs = self.connectivity(neuron_population_id)
        G = nx.Graph()
        for pair in pairs:
            nodes = (self.node_id(pair[0]), self.node_id(pair[1]))
            if (nodes[0] != nodes[1]):
                G.add_edge(*nodes)
        plt.figure()
        nx.draw_kamada_kawai(G, with_labels=True, node_color='#80F0F0', font_size=8)

        pdf_file = f"{neuron_population_id.split(':')[-1]}.pdf"
        print(f'Saving {neuron_population_id} to {pdf_file}')
        plt.savefig(pdf_file)

#===============================================================================

if __name__ == '__main__':

    connectivity = Connectivity('http://sparc-data.scicrunch.io:9000/scigraph')
    for pop_id in range(1, 13):
        connectivity.draw_connectivity_graph(f'ilxtr:neuron-type-keast-{pop_id}')

#===============================================================================
