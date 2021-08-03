from nifstd_tools.simplify import simplify


def query(neupop_id):
    import requests
    url = ('http://sparc-data.scicrunch.io:9000/scigraph/dynamic/'
           f'demos/apinat/neru-3/{neupop_id}?limit=9999999')
    resp = requests.get(url, headers={'Accept': 'application/json'})
    blob = resp.json()
    return blob


def deblob(blob):
    blob = simplify([['apinatomy:target', 'apinatomy:rootOf', 'apinatomy:levels'],
                     ['apinatomy:conveyingLyph', 'apinatomy:topology'],
                     ['apinatomy:conveyingLyph', 'apinatomy:inheritedExternal'],], blob)
    edges = blob['edges']
    for e in edges:
        if e['pred'] == 'apinatomy:target-apinatomy:rootOf-apinatomy:levels':
            e['pred'] = 'apinatomy:next*'
        if e['pred'] == 'apinatomy:conveyingLyph-apinatomy:topology':
            e['pred'] = 'apinatomy:topology*'
        if e['pred'] == 'apinatomy:conveyingLyph-apinatomy:inheritedExternal':
            e['pred'] = 'apinatomy:inheritedExternal*'

    blob['edges'] = [dict(s) for s in set(frozenset({k:v for k, v in d.items()
                                                     if k != 'meta'}.items()) for d in blob['edges'])]
    sos = set(sov for e in blob['edges'] for sov in (e['sub'], e['obj']))
    blob['nodes'] = [n for n in blob['nodes'] if n['id'] in sos]
    somas = [e for e in edges if e['pred'] == 'apinatomy:internalIn']
    externals = [e for e in edges if e['pred'] == 'apinatomy:external']
    ordering_edges = [e for e in edges if e['pred'] == 'apinatomy:next']
    return blob, edges, somas, externals, ordering_edges


def main(blob=None, blob_string=None, neupop_id=None):
    if blob_string is not None:
        import json
        blob = json.loads(result)

    if blob is None:
        blob = query('ilxtr:neuron-type-keast-6')


    blob, edges, somas, externals, ordering_edges = v = deblob(blob)
    return v
