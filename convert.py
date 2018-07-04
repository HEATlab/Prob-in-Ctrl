from stn import STN
from stn import loadSTNfromJSONfile
import json
import math


filename = 'dataset/stp_rubato.json'

with open(filename, 'r') as f:
    jsonObj = json.loads(f.read())

name = "STP Rubato"
jsonSTN = jsonObj["instances"][0][name]


new = STN()
verts = {}
for e in jsonSTN:
    start = e["start_event_name"]
    end = e["end_event_name"]

    if start not in verts:
        verts[start] = len(verts) + 1
        new.addVertex(verts[start])
    if end not in verts:
        verts[end] = len(verts) + 1
        new.addVertex(verts[end])

    if e["type"] == "controllable":
        type = 'stc'
        lb = float(e["properties"]["lb"])
        ub = float(e["properties"]["ub"])
    else:
        type='stcu'
        mean =  float(e["properties"]["distribution"]["mean"])
        std = math.sqrt( float(e["properties"]["distribution"]["variance"]) )
        lb = float(mean - 1.5*std)
        ub = float(mean + 1.5*std)

    if verts[start] in new.uncontrollables and type == 'stcu':
        type = 'stc'

    new.addEdge(verts[start], verts[end], lb, ub, type=type)

outfilename = 'mit4.json'
new.toJSON(outfilename, 'examples/')
