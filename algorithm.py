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
def extractConflict(edges, novel, preds):
    result = []
    for edge in edges:
        entry = (edge.i, edge.j, edge.weight)
        if entry not in novel:
            result.append(edge)
        else:
            result += resolveNovel(edge, novel, preds)

    return result


def resolveNovel(e, novel, preds):
    result = []
    entry = (e.i, e.j, e.weight)
    print(e)
    if entry not in novel:
        result.append(e)
        return result

    labelDist, unlabelDist = preds[e.j]
    distArray = labelDist if e.i in labelDist else unlabelDist

    weight, new_edge = distArray[e.i]
    result.append(distArray[new_edge.j][1])
    result = result + resolveNovel(new_edge, novel, preds)

    return result


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
            return False, extractConflict(edges, novel, preds)
            #return False

    return True, []
    #return True
