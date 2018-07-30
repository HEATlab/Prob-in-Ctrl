from stn import STN
from stn import loadSTNfromJSONfile
from LP import *
from relax import *
from util import *
import matplotlib.pyplot as plt
import glob
import json
import os
import random
import math

##
# \file empirical.py
# \brief perform empirical analysis on our designed metric


# -------------------------------------------------------------------------
# Strong controllability
# -------------------------------------------------------------------------


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

    return new, orig, float(new/orig)



##
# \fn scheduleIsValid(network: STN, schedule: dict) -> STN
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


# -------------------------------------------------------------------------
#  Sample to get success rate
# -------------------------------------------------------------------------

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
# \fn getSchedule(STN, schedule)
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
# \fn sample(STN, success='default', LP='original')
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
        _, bounds, epsilons = originalLP(STN.copy(), super=False, naiveObj=False)
    elif LP == 'proportion':
        _, _, bounds, epsilons = proportionLP(STN.copy())
    else:
        _, _, bounds, epsilons = maxminLP(STN.copy())

    original, shrinked = newInterval(STN, epsilons)
    degree = calculateMetric(original, shrinked)[2]

    schedule = {}
    for i in list(STN.verts.keys()):
        if i not in STN.uncontrollables:
            time = (bounds[(i, '-')].varValue + bounds[(i, '+')].varValue)/2
            schedule[i] = time

    count = 0
    for i in range(50000):
        result = sampleOnce(original, shrinked) if success == 'default' \
                                else altSampleOnce(STN, schedule.copy())
        if result:
            count += 1

    success = float(count/50000)

    return degree, success


##
# \fn sampleAll(listOfFile, success='default', LP='original')
# \brief Compute the success rate for a list of STNUs
#
# @param STN      An STN to test
# @param LP       The type of LP we want to use
#
# @return a list of (degree, success) tuple for STNUs in the list
def sampleAll(listOfFile, success='default', LP='original'):
    result = {}
    for fname in listOfFile:
        p, f = os.path.split(fname)
        print("Processing file: ", f)
        STN = loadSTNfromJSONfile(fname)
        degree, success = sample(STN, success=success, LP=LP)
        result[f] = (degree, success)


    return result



# ---------------------------------
#  Analyze result from the solver
# ---------------------------------


##
# \fn actual_vol(result_name)
# \brief Calculate the actual volume from solver's result
#
# @param result_name        The path to json file that contains solver's result
#
# @return A dictionary in which keys are the name of the network and values are
#         the maximized volume that guarantees strong controllability
def actual_vol(result_name):
    with open(result_name, 'r') as f:
        result = json.loads(f.read())

    actual_Dict = {}
    for x in list(result.keys()):
        v = result[x]
        actual = math.exp(v)
        actual_Dict[x] = actual

    return actual_Dict


##
# \fn compare(actual_Dict)
# \brief Compute the actual and approximated degree of strong controllability
#
# @param actual_Dict        A dictionary containing actual volume
#
# @return A dictionary in which keys are the name of the network and values are
#         (approximation, actual degree)
def compare(actual_Dict):
    dynamic_folder = input("Please input directory with DC STNUs:\n")
    uncertain_folder = input("Please input directory with uncertain STNUs:\n")

    compare_Dict = {}
    for x in list(actual_Dict.keys()):
        actual_volume = actual_Dict[x]

        if x[:7] == 'dynamic':
            fname = os.path.join(dynamic_folder, x + '.json')
        else:
            fname = os.path.join(uncertain_folder, x + '.json')

        STN = loadSTNfromJSONfile(fname)

        _, _, epsilons = originalLP(STN.copy())
        original, shrinked = newInterval(STN, epsilons)

        old, new, degree = calculateMetric(original, shrinked)
        actual = float(actual_volume / old)
        compare_Dict[x] = (degree, actual)

    return compare_Dict



def plot():
    # Plot actual vs approximated
    result_name = input("Please input path to result json file: \n")
    actual_Dict = actual_vol(result_name)
    compare_Dict = compare(actual_Dict)

    L = list(compare_Dict.values())
    x = [d[0] for d in L]
    y = [d[1] for d in L]

    plt.plot(x,y,'o')
    plt.xlim(-0.04, 1.04)
    plt.ylim(-0.04, 1.04)
    plt.xlabel('Approximated degree of strong controllability')
    plt.ylabel('Actual degree of strong controllability')
    plt.title('Accuracy of Approximation Using DSC LP')

    out_folder = input("Please input the output directory:\n")
    fname = os.path.join(out_folder, 'accuracy.png')
    plt.savefig(fname, format='png')
    plt.close()

    # Plot success rate
    dynamic_folder = input("Please input directory with DC STNUs:\n")
    uncertain_folder = input("Please input directory with uncertain STNUs:\n")

    listOfFile = []
    listOfFile += glob.glob(os.path.join(dynamic_folder, '*.json'))
    listOfFile += glob.glob(os.path.join(uncertain_folder, '*.json'))

    resultD_1= sampleAll(listOfFile, success='new')
    result_1 = list(resultD_1.values())
    x_1 = [d[0] for d in result_1]
    y_1 = [d[1] for d in result_1]
    plt.plot(x_1, y_1, 'o')
    plt.xlim(-0.04, 1.04)
    plt.ylim(-0.04, 1.04)
    plt.xlabel("Approximated degree of strong controllability")
    plt.ylabel("Probabiliy of success")
    plt.title("Success rate of ...")

    out_folder = input("Please input the output directory:\n")
    fname = os.path.join(out_folder, 'success_rate.png')
    plt.savefig(fname, format='png')
    plt.close()

# -------------------------------------------------------------------------
# Dynamic controllability
# -------------------------------------------------------------------------


##
# \fn dynamicMetric(STN, new_STN)
# \brief compute the degree of controllability
#
# @param STN        An input STNU
# @param new_STN    Original STNU with contingent intervals shrinked to be DC
#
# @return degree of dynamic controllability
def dynamicMetric(STN, new_STN):
    original = [(-e.Cji, e.Cij) for e in list(STN.contingentEdges.values())]
    shrinked = [(-e.Cji, e.Cij) for e in list(new_STN.contingentEdges.values())]
    return calculateMetric(original, shrinked)


##
# \fn computeDynamic(nlp=True)
# \brief compute degree of controllability for all uncontrollable STNUs we have
#
# @param nlp        Flag indicating whether we want to use NLP
#
# @return A dictionary in which keys are names of the STNU json file and value
#         is the degree of controllability
def computeDynamic(nlp=False):
    uncertain_folder = input("Please input uncertain STNUs folder:\n")
    chain_folder = input("Please input chain STNUs folde:\n")

    listOfFile = []
    listOfFile += glob.glob(os.path.join(uncertain_folder, '*.json'))
    listOfFile += glob.glob(os.path.join(chain_folder, '*.json'))

    degree = {}
    for fname in listOfFile:
        p, f = os.path.split(fname)
        print("Processing: ", f)

        STN = loadSTNfromJSONfile(fname)
        new_STN, count = relaxSearch(STN.copy(), nlp=nlp)

        if not new_STN:
            degree[f] = 0
        else:
            degree[f] = dynamicMetric(STN.copy(), new_STN.copy())[2]

    return degree



##
# \fn generateData(num)
# \brief generate uncontrollable STNUs with decent degree of dynamic
#        controllability
#
# @param num    number of STNUs we want to generate
def generateData(num):
    data_folder = input("Please input destination directory:\n")
    while num != 0:
        new = generateChain(50, 2500)
        result, conflicts, bounds, weight = DC_Checker(new.copy(), report=False)

        if result:
            print("Failed. Dynamically controllable...")
            continue

        new_STN, count = relaxSearch(new.copy(), nlp=False)
        if not new_STN:
            print("Failed. Not able to resolve conflict...")
            continue

        degree = dynamicMetric(new.copy(), new_STN.copy())[2]
        if degree >= 0.2:
            fname = 'new' + str(num) + '.json'
            print("\nGENERATED ONE SUCCESSFUL CHAIN!!!!!!\n")
            new.toJSON(fname, data_folder)
            num -= 1
        else:
            print("Failed. Degree is too small....")



def readNeos(filename, json_folder):
    f = open(filename, 'r')
    for i in range(3):
        line = f.readline()

    obj_value = float(line[17:])
    actual = math.exp(obj_value)

    p, f = os.path.split(filename)
    fname = f[:-4] + '.json'
    json_file = os.path.join(json_folder, fname)

    STN = loadSTNfromJSONfile(json_file)
    result, conflicts, bounds, weight = DC_Checker(STN.copy(), report=False)
    contingent = bounds['contingent']

    total = 1
    for (i,j) in list(STN.contingentEdges.keys()):
        edge = STN.contingentEdges[(i,j)]
        length = edge.Cij + edge.Cji
        total *= length

        if (i,j) not in contingent:
            actual *= length

    return actual, total, float(actual/total)


def processNeos():
    txt_folder = input("Please input folder with txt Neos file:\n")
    json_folder = input("Please input folder with json file:\n")

    result = {}
    text_L = glob.glob(os.path.join(txt_folder, '*.txt'))
    for filename in text_L:
        p, f = os.path.split(filename)
        fname = f[:-4] + '.json'
        print("Processing: ", fname)

        new, orig, degree = readNeos(filename, json_folder)
        result[fname] = {}
        result[fname]['shrinked'] = new
        result[fname]['original'] = orig
        result[fname]['degree'] = degree

    output_folder = input("Please input output folder:\n")
    filename = os.path.join(output_folder, 'result_neos.json')

    with open(filename, 'w') as f:
        json.dump(result, f)

    return result



def processOptimal():
    json_folder = input("Please input folder with json file:\n")
    json_list = glob.glob(os.path.join(json_folder, '*.json'))

    result = {}
    for fname in json_list:
        p, f = os.path.split(fname)
        print("Processing: ", f)

        STN = loadSTNfromJSONfile(fname)
        new_STN, count = relaxSearch(STN.copy())
        new, orig, degree = dynamicMetric(STN.copy(), new_STN.copy())

        result[f] = {}
        result[f]['shrinked'] = new
        result[f]['original'] = orig
        result[f]['degree'] = degree

    output_folder = input("Please input output folder:\n")
    filename = os.path.join(output_folder, 'result_optimal.json')

    with open(filename, 'w') as f:
        json.dump(result, f)

    return result







# -------------------------------------------------------------------------
#  Main function
# -------------------------------------------------------------------------

if __name__ == '__main__':
    #plot()
    print("hello")
