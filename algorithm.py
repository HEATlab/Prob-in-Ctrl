from util import *

##
# \file algorithm.py
# \brief An implementation of the Conflict Generation Algorithm by William
# \note Read Williams 2017 paper for more details on the algorithm implemented:
#       https://www.ijcai.org/proceedings/2017/0598.pdf

# TODO: Implement extractEdgePath, extractConflict
# TODO: Add DAG to DCDijkstra?


##
# \fn DCDijkstra(G, start, preds, novel, callStack, negNodes)
# \brief Determine if there is any semi-reducible negative cycles in an input
#        labeled graph start with the input vertex and identify the edges
#        along the cycle if there is one
#
# @param G              an input labeled graph to check
# @param start          start node
# @param preds          a dictonary of predecessors edges for each vertex
# @param novel          a list of new edges added
# @param callStack      a list keeping track of the recurrence order
# @param negNodes       a list of negative nodes
#
# @return Return True if there is not semi-reducible negative cycle in input
#         labeled graph. Otherwise, return False, the edges along the
#         negative cycle and the end node
def DCDijkstra(G, start, preds, novel, callStack, negNodes):
    Q = PriorityQueue()
    labelDist = {}
    unlabelDist = {}
    labelDist[start] = (0, None)
    unlabelDist[start] = (0, None)

    for edge in G.incomingEdges(start):
        if edge.weight < 0:
            Q.push((edge.i, edge.type), edge.weight)
            if edge.type == edgeType.NORMAL:
                unlabelDist[edge.i] = (edge.weight, edge)
            else:
                labelDist[edge.i] = (edge.weight, edge)


    if start in callStack[:-1]:
        return False, [], start

    preds[start] = (labelDist, unlabelDist)

    while !Q.isEmpty():
        weight, (v, label) = Q.pop()
        if weight >= 0:
            G.addEdge(v, start, weight)
            novel.append((v, start, weight))
            continue

        if v in negNodes:
            callStack.append(v)
            result, edges, end = DCDijkstra(G, v, preds, novel,
                                                        callStack, negNodes)

            if not result:
                ## TODO: Need to implement Extract Path
                if end != None:
                    edges += extractEdgePath(start, v, labelDist, unlabelDist)
                if end == start:
                    end = None
                return False, edges, end

        for edge in G.incomingEdges(v):
            if edge.weight >= 0 and (edge.type != edgeType.LOWER or \
                                                    edge.type != label):
                w = edge.weight + weight
                distArray = labelDist.copy() if edge.type != label \
                                                    else unlabelDist.copy()

                if edge.i not in distArray or w < distArray[edge.i][0]:
                    distArray[edge.i] = (w, edge)
                    Q.addOrDecKey((edge.i, label), w)

    negNodes.remove(start)
    return True, [], None




##
# \fn DC_Checker(STN)
# \brief Check whether an input STNU is dynamically controllable
#
# \details An STNU is dynamically controllable if there is not semi-reducible
#          negative cycles in its labeled graph.
#
# @param STN    an STN which we want to test
#
# @return Return True if the input STNU is dynamically controllable. Otherwise,
#         return False and conflicts.
def DC_Checker(STN):
    G, dict = normal(STN)
    negNodes = G.getNegNodes()
    novel = []
    preds = {}

    for v in negNodes:
        result, edges, end = DCDijkstra(G, v, preds, novel, [v], negNodes)

        if not result:
            # TODO: Need to implement extract Conflict
            return False, extractConflict(edges, novel, preds)

    return True, []
