from util import *

##
# \file algorithm.py
# \brief An implementation of the Conflict Generation Algorithm by William
# \note Read Williams 2017 paper for more details on the algorithm implemented:
#       https://www.ijcai.org/proceedings/2017/0598.pdf

# TODO: Add DAG to DCDijkstra?
# TODO: Test extractConflict



##
# \fn extractEdgePath(s, v, labelDist, unlabelDist)
# \brief Extract the edges along the path from vertex v to vertex s
#
# @param s              end node of the path
# @param v              start node of the path
# @param labelDist      a dictionary holding labeled edges
# @param unlabelDist    a dictionary holding unlabeled edges
#
# @return a list of DC STN edge object that are edges along the path from
#         vertex v to s
def extractEdgePath(s, v, labelDist, unlabelDist):
    result = []

    while True:
        if v in labelDist and v in unlabelDist:
            if not labelDist[v][1]:
                distArray = unlabelDist
            if not unlabelDist[v][1]:
                distArray = labelDist
        elif v in labelDist:
            distArray = labelDist
        else:
            distArray = unlabelDist

        weight, edge = distArray[v]
        result.append(edge)
        v = edge.j

        if edge.j == s:
            break

    return result



##
# \fn extractConflict(STN, edges, dict)
# \brief Extract conflicts in an STN given the edges along the detected
#        semi-reducible negative cycle
#
# @param STN        an input STN to extract conflict
# @param edges      a list of edges along semi-reducible negative cycle
# @param D          a dictionary stores the additional vertices in normal form
#
# @return A dictionary containing conflicts in input STNU
# TODO: In Williams paper, novel and preds are input to this function. Figure
#       out why...
def extractConflict(STN, edges, D):
    # conflicts = {}
    # conflicts['free'] = set()
    # conflicts['contingent'] = set()
    #
    # for e in edges:
    #     start = e.i
    #     end = e.j
    #
    #     if start not in D and end not in D:
    #         orig = STN.getEdge(start, end)
    #         entry = (start, end, 'upper') if orig.i == start \
    #                                         else (end, start, 'lower')
    #         conflicts['free'].add(entry)
    #     elif start in D:
    #         orig = D[start]
    #
    #         if e.type == edgeType.NORMAL:
    #             entry = (orig.i, orig.j, 'lower')
    #             conflicts['contingent'].add(entry)
    #
    #             if end == orig.j:
    #                 entry2 = (orig.i, orig.j, 'upper')
    #                 conflicts['contingent'].add(entry2)
    #
    #     else:
    #         orig = D[end]
    #         if e.type == edgeType.UPPER:
    #             entry1 = (orig.i, orig.j, 'lower')
    #             entry2 = (orig.i, orig.j, 'upper')
    #             conflicts['contingent'].add(entry1)
    #             conflicts['contingent'].add(entry2)
    #         elif start == orig.i:
    #             entry = (orig.i, orig.j, 'lower')
    #             conflicts['contingent'].add(entry)

    return edges




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
            Q.push((edge.i, edge.parent), edge.weight)
            if edge.parent == None:
                unlabelDist[edge.i] = (edge.weight, edge)
            else:
                labelDist[edge.i] = (edge.weight, edge)

    if start in callStack[1:]:
        return False, [], start
        #return False

    preds[start] = (labelDist, unlabelDist)

    while not Q.isEmpty():
        weight, (v, label) = Q.pop()

        if weight >= 0:
            G.addEdge(v, start, weight)
            novel.append((v, start, weight))
            continue

        if v in negNodes:
            newStack = [v] + callStack
            result, edges, end = DCDijkstra(G, v, preds, novel, newStack, negNodes)
            # result = DCDijkstra(G, v, preds, novel, newStack, negNodes)

            if not result:
                if end != None:
                   edges += extractEdgePath(start, v, labelDist, unlabelDist)
                if end == start:
                   end = None
                return False, edges, end
                # return False

        for edge in G.incomingEdges(v):
            if edge.weight >= 0 and (edge.type != edgeType.LOWER or \
                                                        edge.parent != label):
                w = edge.weight + weight
                distArray = labelDist if label != None else unlabelDist

                if edge.i not in distArray or w < distArray[edge.i][0]:
                    distArray[edge.i] = (w, edge)
                    Q.addOrDecKey((edge.i, label), w)

    negNodes.remove(start)
    return True, [], None
    # return True



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
    G, D = normal(STN)
    negNodes = G.getNegNodes()
    novel = []
    preds = {}

    for v in negNodes:
        result, edges, end = DCDijkstra(G, v, preds, novel, [v], negNodes.copy())
        #result = DCDijkstra(G, v, preds, novel, [v], negNodes.copy())
        #print(v, result)

        if not result:
            return False, extractConflict(STN, edges, D)
            #return False

    return True, []
    #return True
