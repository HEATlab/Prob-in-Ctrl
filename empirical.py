from stn import STN
from stn import loadSTNfromJSONfile
from LP import *
import glob
import json
import os
import random
import matplotlib.pyplot as plt

##
# \file empirical.py
# \brief perform empirical analysis on our designed metric


##
# \fn newInterval(STN, epsilons)
# \brief compute shrinked contingent intervals
#
# @param STN            an input STN
# @param epsilons       a dictionary of epsilons returned by our LP
#
# @return Return a list of original contingent intervals and a list of shrinked
#         contingent intervals
def newInterval(STN, epsilons):
    original = []
    shrinked = []
    for edge in list(STN.contingentEdges.values()):
        orig = (-edge.Cji, edge.Cij)
        original.append(orig)

        low, high = epsilons[(edge.j, '-')].varValue, epsilons[(edge.j, '+')].varValue
        new = (-edge.Cji+low, edge.Cij-high)
        shrinked.append(new)

    return original, shrinked


##
# \fn calculateMetric(original, shrinked)
# \brief Compute our degree of strong controllability
#
# @param original       A list of original contingent intervals
# @param shrinked       A list of shrinked contingent intervals
#
# @return the value of degree of strong controllability
def calculateMetric(original, shrinked):
    orig = 1
    new = 1
    for i in range(len(original)):
        x, y = original[i]
        orig *= (y-x)

        a, b = shrinked[i]
        new *= (b-a)

    return float(new/orig)

##
# \fn sampleOnce(original, shrinked)
# \brief Check whether a randomly generated realization is inside strong
#        controllable region
#
# @param original       A list of original contingent intervals
# @param shrinked       A list of shrinked contingent intervals
#
# @return Return True if the random realization falls into the strongly
#         controllable region. Return False otherwise
def sampleOnce(original, shrinked):
    for i in range(len(original)):
        x,y = original[i]
        a,b = shrinked[i]

        real = random.uniform(x, y)
        #print(original[i], shrinked[i], real)
        if real < a or real > b:
            return False

    return True

##
# \fn scheduleIsValid(network, schedule)
# \brief Given an STNU and schedule, checks if the schedule is valid or not.
#
# @param network       An input STNU
#
# @param schedule      A dictionary whose keys are vertex IDs and whose values
#                      are the times selected for those events.
#
# @return              True/False if the schedule is valid/invalid.
def scheduleIsValid(network: STN, schedule: dict) -> STN:
    # Check that the schedule is actually defined on all relevant vertices
    epsilon = 0.001
    vertices = network.getAllVerts()
    for vertex in vertices:
        vertexID = vertex.nodeID
        assert vertexID in schedule

    # Check that the schedule is valid
    edges = network.getAllEdges()
    for edge in edges:
        # Loop through the constraints
        start = edge.i
        fin   = edge.j
        uBound = edge.Cij
        lBound = -edge.Cji

        boundedAbove = (schedule[fin] - schedule[start]) <= uBound + epsilon
        boundedBelow = (schedule[fin] - schedule[start]) >= lBound - epsilon

        # Check if constraint is not satisfied
        if ((not boundedAbove) or (not boundedBelow)):
            return False

    return True


##
# \fn getSchedule(STN, bounds, schedule)
# \brief Construct a possible schedule for an STN given a fixed decision
#
# @param STN            An STNU we want to test
# @param schedule       A dictionary with the fixed decision
#
# @return a schedule for the given STNU
def getSchedule(STN, schedule):
    for edge in list(STN.contingentEdges.values()):
        start_time = schedule[edge.i]
        real = random.uniform(-edge.Cji, edge.Cij)
        time = start_time + real
        schedule[edge.j] = time
    return schedule


##
# \fn altSampleOnce(STN, schedule)
# \brief Another strategy of sampling to test strong controllability
#
# @param STN            An STNU we want to test
# @param schedule       A dictionary with the fixed decision
#
# @return Return True if the schedule generate is valid. Return False otherwise
def altSampleOnce(STN, schedule):
    s = getSchedule(STN, schedule)
    if scheduleIsValid(STN, s):
        return True
    return False



##
# \fn sample(STN, LP='original')
# \brief Compute the success rate of an STNU by randomly sample 50000 times
#
# \note There are three kinds of LPs we can use to compute the amount of
#       uncertainty removed from each contingent interval
#
# @param STN      An STN to test
# @param LP       The type of LP we want to use
#
# @return The degree of controllability and the success rate for input STN
def sample(STN, success='default', LP='original'):
    if LP == 'original':
        _, bounds, epsilons = originalLP(STN.copy(), super=False, naiveObj = False)
    elif LP == 'proportion':
        _, _, bounds, epsilons = proportionLP(STN.copy())
    else:
        _, _, bounds, epsilons = maxminLP(STN.copy())

    original, shrinked = newInterval(STN, epsilons)
    degree = calculateMetric(original, shrinked)

    schedule = {}
    for i in list(STN.verts.keys()):
        if i not in STN.uncontrollables:
            time = (bounds[(i, '-')].varValue + bounds[(i, '+')].varValue)/2
            schedule[i] = time

    count = 0
    for i in range(1000):
        result = sampleOnce(original, shrinked) if success == 'default' \
                                else altSampleOnce(STN, schedule.copy())
        if result:
            count += 1

    success = float(count/1000)

    return degree, success


##
# \fn sampleAll(listOfFile, LP='original')
# \brief Compute the success rate for a list of STNUs
#
# @param STN      An STN to test
# @param LP       The type of LP we want to use
#
# @return a list of (degree, success) tuple for STNUs in the list
def sampleAll(listOfFile, success='default', LP='original'):
    result = {}
    weird = {}
    for fname in listOfFile:
        p, f = os.path.split(fname)
        print("Processing file: ", f)
        STN = loadSTNfromJSONfile(fname)
        degree, success = sample(STN, success=success, LP=LP)
        result[f] = (degree, success)

        if degree - success >= 0.1:
            weird[f] = (degree, success)

    return result, weird



# if __name__ == '__main__':
#     listOfFile = []
#     listOfFile += glob.glob(os.path.join('../../../examples/dynamic/', '*.json'))
#     listOfFile += glob.glob(os.path.join('../../../examples/uncertain/', '*.json'))
#     listOfFile += glob.glob(os.path.join('../../../examples/chain/', '*.json'))
#
#     print("Testing with Original LP...\n")
#     resultD_1, weird1 = sampleAll(listOfFile, success='new')
#     result_1 = list(resultD_1.values())
#     x_1 = [d[0] for d in result_1]
#     y_1 = [d[1] for d in result_1]
#     plt.plot(x_1, y_1, 'o')
#     plt.xlim(-0.04, 1.04)
#     plt.ylim(-0.04, 1.04)
#     plt.xlabel("Degree of strong controllability")
#     plt.ylabel("Success rate")
#     plt.title("Original LP")
#
#     fname = os.path.join('../../../', 'original_obj.png')
#     plt.savefig(fname, format='png')
#     plt.close()
