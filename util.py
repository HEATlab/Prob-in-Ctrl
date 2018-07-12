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

        L = [random.randint(0, 150) for i in range(task)]
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
        new.addEdge(0,task*2, 0, makespan)

        print("Checking Consistensy...")
        if new.isConsistent():
            return new
