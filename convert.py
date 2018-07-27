from stn import STN
from stn import loadSTNfromJSONfile
from algorithm import *
from util import *
import json
import math


filename = '../../../dataset/car_sharing.json'

print("Start reading file...")
with open(filename, 'r') as f:
   jsonObj = json.loads(f.read())

out_folder1 = '../../../uncertain/'
out_folder2 = '../../../dynamic/'

print("Start converting...")
uncertainIndex = 32
dynamicIndex = 453
for stn in jsonObj["instances"]:
    name = list(stn.keys())[0]
    jsonSTN = stn[name]
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
            lb = round(float(e["properties"]["lb"]), 3)
            ub = round(float(e["properties"]["ub"]), 3)
        elif e["type"] == "uncontrollable_bounded":
            type = 'stcu'
            lb = round(float(e["properties"]["lb"]), 3)
            ub = round(float(e["properties"]["ub"]), 3)
        elif e["properties"]["distribution"]["type"] == "uniform":
            type='stcu'
            lb = round(float(e["properties"]["distribution"]["lb"]), 3)
            ub = round(float(e["properties"]["distribution"]["ub"]), 3)
        else:
            type='stcu'
            mean =  float(e["properties"]["distribution"]["mean"])
            std = math.sqrt( float(e["properties"]["distribution"]["variance"]) )
            lb = round(float(mean - 0.5*std), 3)
            ub = round(float(mean + 0.5*std), 3)

        if verts[start] in new.uncontrollables and type == 'stcu':
            type = 'stc'

        new.addEdge(verts[start], verts[end], lb, ub, type=type)

    print("Check for Consistensy...")
    if not new.isConsistent():
        print("Not consistent...\n")
        continue


    print("Check for Dynamic Controllability...")
    #result, conflicts, bounds, weight = DC_Checker(new.copy())
    result = dc_checking(new.copy())
    if result == False:
        print("Generated an uncertain STNU...\n")
        fname = 'uncertain' + str(uncertainIndex) + '.json'
        new.toJSON(fname, out_folder1)
        uncertainIndex += 1
    elif result == True:
        print("Generated a dynamic STNU...\n")
        fname = 'dynamic' + str(dynamicIndex) + '.json'
        new.toJSON(fname, out_folder2)
        dynamicIndex += 1
