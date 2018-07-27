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
    all_uncontrollables = set(network.uncontrollables)
    unused_events = set(network.verts.keys())
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
            if (edge.j == activated_event) and (edge.i not in all_uncontrollables):
                if needs_early_update(edge, activated_event, current_time, true_weight):
                    lower_bound = current_time - edge.Cij
                    true_weight[edge.i] = lower_bound
        
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
# @return A bool which is True if and only if execution is successful
def simulate_once(network: STN, is_early: bool) -> bool:
    # Generate the realization
    realization = {}
    for nodes, edge in network.contingentEdges.items():
        realization[node[1]] = random.uniform(-edge.Cji, edge.Cij)
    
    # Run the simulation
    if is_early:
        return early_execution(network, realization)
    else:
        return late_execution(network, realization)


# -------------------------------------------------------------------------
#  Simulation Helpers
# -------------------------------------------------------------------------
##
# \fn needs_early_update()
# \brief Checks if the endpoint of a particular edge needs to have its
#        planned time updated in early execution
#
# @param edge
# @param fixed_event
# @param fixed_value
# @param planned_times
# 
# @return True if and only if we should modify the edge's source vertex
def needs_early_update(edge, fixed_event, fixed_value, planned_times):
    new_time = fixed_value - edge.Cij
    if new_time > planned_times[edge.i]:
        return True

# -------------------------------------------------------------------------
#  Modify Networks
# -------------------------------------------------------------------------
##
# \fn find_bounds(network)
# \brief 
#
# @param network      The STNU to compute bounds for early execution.
#
# @return A dictionary from controllable events to the implied lower and
#         upper bounds (lb, ub) relative to the zero time point
def find_bounds(network: STN) -> dict:
    # Add zero timepoint
    if ZERO_ID not in network.verts:
        network.addVertex(ZERO_ID)
    # Add bounds relative to zero timepoint
    adjacent_to_zero = set(network.getAdjacent(ZERO_ID))
    events = network.verts.keys()
    bounds = {}
    for event in events:
        if (event != ZERO_ID) and (event not in adjacent_to_zero):
            return 0
        else:
            return 0
    
    # To make sure zero timepoint starts first
    bounds[ZERO_ID] = (-1.0, 0.0)
    return bounds


##
# \fn set_dynamic_zeropoint(network)
# \brief
# 
# @param
# @param
def set_dynamic_zeropoint(network: STN):
    return 0
