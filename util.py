from stn import STN
from stn import loadSTNfromJSONfile
from dc_stn import DC_STN, edgeType
import random

##
# \file util.py
# \brief helpful functions

##
# \fn STNtoDCSTN(S)
# \brief Convert an STN object to a DC_STN object
#
# @param S  An input STN object to convert
#
# @return A DC_STN object that has the same vertices and edges as the input
def STNtoDCSTN(S):
    new_STN = DC_STN()
    for edge in list(S.edges.values()):
        new_STN.addEdge(edge.i,edge.j,edge.Cij)
        new_STN.addEdge(edge.j,edge.i,edge.Cji)
        if edge.isContingent():
            new_STN.addEdge(edge.i, edge.j, -edge.Cji,
                                    edge_type=edgeType.LOWER,parent=edge.j)
            new_STN.addEdge(edge.j, edge.i, -edge.Cij,
                                    edge_type=edgeType.UPPER,parent=edge.j)
    return new_STN



##
# \fn dc_checking(STN)
# \brief Check if an input STN is dynamically controllable
#
# @param S  An input STN object to check
#
# @return Return True if the input STN is dynamically controllable. Return
#         False otherwise.
def dc_checking(STN):
    return STNtoDCSTN(STN).is_DC()



##
# \fn dc_checking(filename)
# \brief Check if an input STN is dynamically controllable
#
# @param filename  An input STN object to check
#
# @return Return True if the input STN is dynamically controllable. Return
#         False otherwise.
def dc_checking_file(filename):
    STN = loadSTNfromJSONfile(filename)
    return dc_checking(STN)



##
# \fn generateChain(task, free)
# \brief generate a consistent STNUs in a chainlike structure
#
# \details The chainlike STNU is very common in real life application, such as
#          AUV need to drive to different sites and complete task at each site.
#          Driving to different cite is contingent, but the agent can decide
#          how long it takes to complete the task.
#
# @param task  The number of tasks need to be completed
# @param free  The total length of the free constraint intervals we want
#              in the generated STNU
#
# @return Return the generated STNU
def generateChain(task, free):
    totalEvent = 2 * (task+1)

    while True:
        new = STN()
        for i in range(totalEvent):
            new.addVertex(i)

        L = [random.randint(0, 100) for i in range(task)]
        s = sum(L)
        L = [int(x/s*free) for x in L]
        diff = free - sum(L)
        L[-1] += diff

        bounds = []
        for i in range(totalEvent-1):
            type = 'stcu' if i % 2==0 else 'stc'
            if type == 'stcu':
                lowBound = random.randint(0,50)
                length = random.randint(0,50)
                bounds.append((lowBound, lowBound+length))
                new.addEdge(i, i+1, lowBound, lowBound+length, type='stcu')
            else:
                lowBound = random.randint(0,100)
                length = L[int((i-1)/2)]
                bounds.append((lowBound, lowBound+length))
                new.addEdge(i, i+1, lowBound, lowBound+length)

        low = sum([x[0] for x in bounds])
        up = sum([x[1] for x in bounds])
        makespan = random.randint(low, up)
        new.addEdge(0,task*2+1, 0, makespan)

        print("Checking Consistensy...")
        if new.isConsistent():
            return new



##
# \fn normal(STN)
# \brief convert a given STNU to its normal form labeled graph using DC_STN
#
# \details  a normal form labeled graph is needed for Williams algorithm.
#           The robotbrunch DC_STN class keeps track of the upper, lower case
#           edges, so we need to use it for labeled graph.
#
# @param STN  an STN to convert
#
# @return Return the DC_STN that is the normal form labeled graph for input STN
#         and a dictionary storing vertices added to create normal form
def normal(STN):
    new = DC_STN()
    for i in list(STN.verts.keys()):
        new.addVertex(i)

    changed = {}
    for e in list(STN.edges.values()):
        if not e.isContingent():
            new.addEdge(e.i, e.j, e.Cij)
            new.addEdge(e.j, e.i, e.Cji)
        else:
            if e.Cji != 0:
                new_vert = len(new.verts)
                changed[new_vert] = (e.i, e.j, -e.Cji, e.Cij)
                new.addVertex(new_vert)


                new.addEdge(e.i, new_vert, -e.Cji)
                new.addEdge(new_vert, e.i, e.Cji)

                upper = e.Cij + e.Cji
                new.addEdge(new_vert, e.j, upper)
                new.addEdge(e.j, new_vert, 0)
                new.addEdge(new_vert, e.j, 0, edge_type=edgeType.LOWER,
                                                                parent=e.j)
                new.addEdge(e.j, new_vert, -upper, edge_type=edgeType.UPPER,
                                                                parent=e.j)
            else:
                new.addEdge(e.i, e.j, e.Cij)
                new.addEdge(e.j, e.i, e.Cji)
                new.addEdge(e.i, e.j, -e.Cji, edge_type=edgeType.LOWER,
                                                                parent=e.j)
                new.addEdge(e.j, e.i, -e.Cij, edge_type=edgeType.UPPER,
                                                                parent=e.j)
    return new, changed
