from util import PriorityQueue
from stn import STN
import random

##
# \file simulation.py
# \brief Hosts some cheap implementations of dynamic execution strategies on STNUs

MAX_FLOAT = 100000000000000000.0

##
# \fn early_execution(network, realization)
# \brief Runs an STNU simulation where the agent follows an early execution strategy
#
# @param network       STNU we will run simulation on
# @param realization   Dictionary from contingent edge values to nonnegative reals
# 
# @return A bool, which is True if and only if the execution is successful
def early_execution(network: STN, realization: dict) -> bool:
    return False

##
# \fn late_execution(network, realization)
# \brief Runs an STNU simulation where the agent follows the late dynamic strategy
#
# @param network       STNU we will run simulation on
# @param realization   Dictionary from contingent edge values to nonnegative reals
# 
# @return A bool, which is True if and only if the execution is successful
def late_execution(network: STN, realization: dict) -> bool:
    return True

##
# \fn simulate_once(network, is_early)
# \brief Generate a realization randomly, and simulate execution of the network for
#        that realization
# 
# @param network      STNU we run the simulation on
# @param is_early     Boolean indicating whether we use early (True) or late (False)
#                     strategy
# 
# @return A bool which is True if and only if execution is succesful
def simulate_once(network: STN, is_early: bool) -> bool:
    # Generate the realization
    realization = {}

    
    # Run the simulation
    if is_early:
        return early_execution(network, realization)
    else:
        return late_execution(network, realization)


# -------------------------------------------------------------------------
#  Modify Networks
# -------------------------------------------------------------------------
##
# \fn find_bounds(network)
# \brief 
#
# @param
# @param
#
# @return 
def find_bounds(network: STN) -> dict:
    return {}


##
# \fn add_zeropoint(network, is_contingent)
# \brief
# 
# @param
# @param
def add_zeropoint(network: STN, is_contingent: bool):
    return 0
