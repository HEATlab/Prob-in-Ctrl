from util import PriorityQueue
from stn import STN
from empirical import scheduleIsValid
import random

##
# \file simulation.py
# \brief Hosts some cheap implementations of dynamic execution strategies on STNUs
# \note This file assumes that any event with id zero is necessarily the zero timepoint

MAX_FLOAT = 100000000000000000.0
ZERO_ID = 0

##
# \fn early_execution(network, realization)
# \brief Runs an STNU simulation where the agent follows an early execution strategy
#
# @param network       STNU we will run simulation on
# @param realization   Dictionary from uncontrollables to contingent edge values
# 
# @return A bool, which is True if and only if the execution is successful
def early_execution(network: STN, realization: dict) -> bool:
    ## Bookkeeping for events
    unused_events = set(self.verts.keys())
    not_scheduled = PriorityQueue()
    final_schedule = {}

    # Mapping from contingent sources to uncontrollables
    contingent_pairs = network.contingentEdges.keys()
    disabled_uncontrollables = {src: sink for (src, sink) in contingent_pairs}
    
    # Initialize bounds for simulation - starts off with just controllables
    # and zero time point
    controllable_bounds = find_bounds(network)
    true_weight = {}
    for event in controllable_bounds:
        not_scheduled.push(event, controllable_bounds[0])
        true_weight[event] = controllable_bounds[0]
    not_scheduled.addOrDecKey(ZERO_ID, 0)

    # Run simulation
    old_time = 0
    while len(unused_events) > 0:
        current_time, activated_event = not_scheduled.pop()
        
        # This check ensures that we popped out a valid time_point
        # A better way to deal with this would be to just figure out a way to 
        # increase priorities of elements in a heap
        if activated_event in true_weight:
            if true_weight[activated_event] > current_time:
                continue
        
        unused_events.remove(activated_event) 
        final_schedule[activated_event] = current_time 

        assert old_time < current_time, "Chronology violated!"
        
        if activated_event in disabled_uncontrollables:
            # If this is a contingent source, we add the associated uncontrollable sink
            # to the queue
            uncontrollable = disabled_uncontrollables[activated_event]
            delay = realization[uncontrollable]
            not_scheduled.push(uncontrollable, current_time + delay)
        
        # Update the bounds for all other timepoints
        # We only care about events being moved later in time
        relevant_edges = self.getEdges(activated_event)
        for edge in relevant_edges:
            if edge.j == activated_event:
                lower_bound = current_time - edge.Cij
                if lower_bound > true_weight[activated_event]:
                    true_weight[activated_event] = lower_bound
        
        # Keep track of this for next iteration of loop
        old_time = current_time
    # Check if we dispatched succesfully
    if scheduleIsValid(network, final_schedule):
        return False
    else:
        return True


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
# @param network      The STNU to compute bounds for
#
# @return A dictionary from controllable events to the implied lower and
#         upper bounds (lb, ub) relative to the zero time point
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