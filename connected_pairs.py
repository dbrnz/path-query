from pprint import pprint
import requests

from nifstd_tools.simplify import apinat_deblob
from nifstd_tools.simplify import ematch, sub, pred, obj, endIn, fasIn, layerIn, ie, ext


def query(neupop_id):
    url = ('http://sparc-data.scicrunch.io:9000/scigraph/dynamic/'
           f'demos/apinat/neru-4/{neupop_id}.json?limit=9999999')
    resp = requests.get(url, headers={'Accept': 'application/json'})
    blob = resp.json()
    return blob

def isLayer(s):
    return ematch(blob, (lambda e, m: sub(e, m) and pred(e, layerIn)), s)


def lay_reg(start):
    direct = [obj(t) for t in
              ematch(blob, (lambda e, m: sub(e, m)
                            and (pred(e, intIn) or
                                 pred(e, endIn) or
                                 pred(e, fasIn))),
                     start)]

    layers = [obj(t) for d in direct for t in
              ematch(blob, (lambda e, m: sub(e, m)
                            and isLayer(m)
                            and (pred(e, ie) or
                                 pred(e, ext))),
                     d)]

    lregs = []
    if layers:
        ldir = [obj(t) for d in direct for t in
                ematch(blob, (lambda e, m: sub(e, m)
                              and pred(e, layerIn)),
                       d)]

        lregs = [obj(t) for d in ldir for t in
                 ematch(blob, (lambda e, m: sub(e, m)
                               and not isLayer(m)
                               and (pred(e, ie) or
                                    pred(e, ext))),
                        d)]

    regions = [obj(t) for d in direct for t in
               ematch(blob, (lambda e, m: sub(e, m)
                             and not isLayer(m)
                             and (pred(e, ie) or
                                  pred(e, ext))),
                      d)]

    assert not (lregs and regions), (lregs, regions)  # not both
    regions = lregs if lregs else regions
    out = start, layers[0] if layers else None, regions[0] if regions else None
    if out:
      return out


blob_raw = query('ilxtr:neuron-type-keast-5')

blob, *_ = apinat_deblob(blob_raw)

starts = [obj(e) for e in blob['edges'] if pred(e, 'apinatomy:lyphs')]

nxt = 'apinatomy:next'
nxts = 'apinatomy:next*'
intIn = 'apinatomy:internalIn'

nexts = [(sub(t), obj(t)) for start in starts for t in
         ematch(blob, (lambda e, m: pred(e, nxt) or pred(e, nxts)), None)]


connected_pairs = sorted(set([tuple([lay_reg(e) for e in p]) for p in nexts]))
pprint(connected_pairs)
connected_pairs
