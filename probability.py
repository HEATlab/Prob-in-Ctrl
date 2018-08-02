from algorithm import DC_Checker
from stn import STN, loadSTNfromJSONfile
from relax import relaxSearch

from scipy.stats import norm
from math import sqrt, log, exp
from typing import List

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
# \fn special_prob()
# \brief Returns the closed form answer that should only work in a special case.
def special_prob(lengths: list, S: float) -> float:
    n = len(lengths)
    # Get the logarithm of the relevant expression
    numerator = n * log(sum(lengths))

    log_lengths = [log(l) for l in lengths]
    log_factorial = [log(m) for m in range(1, n+1)]
    denominator = sum(log_lengths) + sum(log_factorial)

    log_prob = numerator - denominator
    true_prob = exp(log_prob)
    return true_prob

##
# \fn prob_of_DC_file()
def prob_of_DC_file(file_name: str) -> float:
    network = loadSTNfromJSONfile(file_name)
    return prob_of_DC(network)

def prob_of_multiple_conflicts(lengths_list: List[list], weights: List[float]):
    probability = 1.0
    m = len(lengths_list)
    assert len(weights) == m, "The input lists have different lengths!"

    for j in range(m):
        probability = probability * (prob_small_sum(lengths_list[j], weights[j]))

    return probability

##
# \fn prob_of_DC()
def prob_of_DC(network: STN) -> float:
    _, num_conflicts, cycles, neg_weights = relaxSearch(network)

    lengths_list = [[] for j in range(num_conflicts)]
    weights_list = []

    for j in range(num_conflicts):
        edges = cycles[j]
        for edge in edges:
            lengths_list[j].append(edge.getWeightMax() - edge.getWeightMin())

        S = sum(lengths_list[j]) + neg_weights[j]
        weights_list.append(S)

    return prob_of_multiple_conflicts(lengths_list, weights_list)

def main():
    # rel_path = "stnudata/uncertain/"
    # beg = "uncertain"
    beg = "new_uncertain"
    end = ".json"

    rel_path = "stnudata/more_uncertain/"
    good_list = [2]
    # bad_set = {17}
    # good_list = [7]
    # good_list = range(1,32)
    bad_set = set()
    file_names = [f"{rel_path}{beg}{j}{end}" for j in good_list if j not in bad_set]

    for name in file_names:
        res = prob_of_DC_file(name)
        print(f"{name} is expected to succeed {100*res}% of the time.")

if __name__ == "__main__":
    main()
