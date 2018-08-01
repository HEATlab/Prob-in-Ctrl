from algorithm import DC_Checker
from stn import STN, loadSTNfromJSONfile
from relax import relaxSearch

from scipy.stats import norm
from math import sqrt

##
# \file probability.py
# \brief Computing some probabilities for degree of dynamic controllability

##
# \fn prob_small_sum(lengths, S)
# \brief
#
# @param lengths   An array of the lengths l_i
# @param S         A sum the (a_i)s should be less than
#
# @return          The probability that a_1 + ... + a_n <= S given
#                  that a_i ~ U(0, l_i)
def prob_small_sum(lengths: list, S: float) -> float:
    mean = 0.0
    variance = 0.0
    N = len(lengths)

    for l in lengths:
        mean += l
        variance += l*l
    mean = mean/2
    variance = variance/12

    z_score = (S - mean)/sqrt(variance)

    return norm.cdf(z_score)

##
# \fn prob_of_DC_file()
def prob_of_DC_file(file_name: str) -> float:
    network = loadSTNfromJSONfile(file_name)
    return prob_of_DC(network)

##
# \fn prob_of_DC()
def prob_of_DC(network: STN) -> float:
    is_controllable, _, bounds, neg_weight = DC_Checker(network, False)

    if is_controllable:
        print("It's controllable tho!")
        return False

    edge_dict = bounds['contingent']

    lengths = []
    for nodes, edge in edge_dict.items():
        lengths.append(edge[0].getWeightMax() - edge[0].getWeightMin())

    S = sum(lengths) + neg_weight

    return prob_small_sum(lengths, S)


def prob(network: STN) -> float:
    _, _, cycles = relaxSearch(network.copy())

    if cycles == None:
        print("Cannot resolve...")
        return False

    if cycles == []:
        print("It's controllable tho!")
        return False

    p = 1
    for bounds, neg_weight in cycles:
        edge_dict = bounds['contingent']

        lengths = []
        for nodes, edge in edge_dict.items():
            lengths.append(edge[0].Cij + edge[0].Cji)

        S = sum(lengths) + neg_weight
        print(prob_small_sum(lengths, S))
        p *= prob_small_sum(lengths, S)

    return p
