from stn import STN
from stn import loadSTNfromJSONfile
from dc_checking import dc_checking
import json
import math


filename = 'dataset/rover_coordination_small_less_activities.json'

with open(filename, 'r') as f:
    jsonObj = json.loads(f.read())

# out directory
strong_directory = '../../../examples/strong/'
dynamic_directory = '../../../examples/dynamic/'
uncertain_directory = '../../../examples/uncertain/'


strongIndex = 9
dynamicIndex = 5
uncertainIndex = 5
for stn in jsonObj["instances"]:
    name = list(stn.keys())[0]
    jsonSTN = stn[name]
    new = STN()
    verts = {}

    print("Processing:", name)
    count += 1
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
        elif e["type"] == "uncontrollable_bounded":
            type = 'stcu'
            lb = float(e["properties"]["lb"])
            ub = float(e["properties"]["ub"])
        elif e["properties"]["distribution"]["type"] == "uniform":
            type='stcu'
            lb = float(e["properties"]["distribution"]["lb"])
            ub = float(e["properties"]["distribution"]["ub"])
        else:
            type='stcu'
            mean =  float(e["properties"]["distribution"]["mean"])
            std = math.sqrt( float(e["properties"]["distribution"]["variance"]) )
            lb = float(mean - 1.5*std)
            ub = float(mean + 1.5*std)

        if verts[start] in new.uncontrollables and type == 'stcu':
            type = 'stc'

        new.addEdge(verts[start], verts[end], lb, ub, type=type)

    if new.isStronglyControllable():
        fname = 'strong' + str(strongIndex) + '.json'
        new.toJSON(fname, strong_directory)
        strongIndex += 1

    elif dc_checking(new):
        fname = 'dynamic' + str(dynamicIndex) + '.json'
        new.toJSON(fname, dynamic_directory)
        dynamicIndex += 1

    else:
        fname = 'uncertain' + str(uncertainIndex) + '.json'
        new.toJSON(fname, uncertain_directory)
        uncertainIndex += 1
