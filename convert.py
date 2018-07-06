from stn import STN
from stn import loadSTNfromJSONfile
from dc_checking import dc_checking
import json
import math


filename = 'car_sharing.json'

with open(filename, 'r') as f:
    jsonObj = json.loads(f.read())

print("Finished reading file...")
# out directory
strong_directory = '../../../examples/strong/'
dynamic_directory = '../../../examples/dynamic/'
uncertain_directory = '../../../examples/uncertain/'


strongIndex = 440
dynamicIndex = 451
uncertainIndex = 5
count = 1
nameDic = {}
probDic = {}
for stn in jsonObj["instances"]:
    name = list(stn.keys())[0]
    jsonSTN = stn[name]
    new = STN()
    verts = {}

    print("Processing:", name, count)
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

        if (verts[start], verts[end]) in new.edges or (verts[end], verts[start]) in new.edges:
            if name not in probDic:
                probDic[name] = [(verts[start], verts[end])]
            else:
                probDic[name].append((verts[start], verts[end]))
        else:
            new.addEdge(verts[start], verts[end], lb, ub, type=type)


    if new.isStronglyControllable():
        fname = 'strong' + str(strongIndex) + '.json'
        nameDic[name] = fname
        new.toJSON(fname, strong_directory)
        strongIndex += 1

    elif dc_checking(new):
        fname = 'dynamic' + str(dynamicIndex) + '.json'
        nameDic[name] = fname
        new.toJSON(fname, dynamic_directory)
        dynamicIndex += 1

    else:
        fname = 'uncertain' + str(uncertainIndex) + '.json'
        nameDic[name] = fname
        new.toJSON(fname, uncertain_directory)
        uncertainIndex += 1
