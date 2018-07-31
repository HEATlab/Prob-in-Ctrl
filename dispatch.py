from stn import STN, loadSTNfromJSONfile
from util import STNtoDCSTN, PriorityQueue
from dc_stn import DC_STN
from empirical import scheduleIsValid

import random

##
# \file dispatch.py
# \brief Hosts method to dispatch STNUs that were modified by the
#        old dynamic checking algorithm
# \note More exposition can be found in: 
#       https://pdfs.semanticscholar.org/0313/af826f45d090a63fd5d787c92321666115c8.pd

ZERO_ID = 0


##
# \fn simulation(network, size)
def simulation(network: STN, size: int) -> float:
    total_victories = 0
    dc_network = STNtoDCSTN(network)

    # Some data useful from the original network
    contingent_pairs = network.contingentEdges.keys()
    contingents = {src: sink for (src, sink) in contingent_pairs}

    # Running the simulation
    for j in range(size):
        realization = generate_realization(network)
        result = dispatch(network, dc_network.copy(), realization, contingents)
        print("Completed a simulation.")
        if result:
            total_victories += 1
    
    return float(total_victories/size)

##
# \fn dispatch(network)
def dispatch(network: STN, dc_network: DC_STN, realization: dict, 
        contingent_map: dict) -> bool:
    ## For dealing with uncontrollables
    uncontrollable_events = set(contingent_map.values())

    # uncontrollable_times = PriorityQueue()

    ## Turn the STNU into the old class
    dc_network.addVertex(ZERO_ID)

    ## Modify the network
    controllability = dc_network.is_DC()
    # print(dc_network)

    ## Dispatch the modified network
    # Assume we have a zero reference point
    enabled = {ZERO_ID}
    not_executed = set(dc_network.verts.keys())
    executed = set()
    current_time = 0.0
    
    schedule = {}

    time_windows = {event: [0, float('inf')] for event in not_executed}

    # print("Beginning dispatch...")
    while len(not_executed) > 0:
        # Find next event to execute
        min_time = float('inf')

        # print("\n\nNetwork looks like: ")
        # print(dc_network)

        # print("Current time windows: ", time_windows)
        # print("Currently enabled: ", enabled)
        # print("Already executed: ", executed)
        # print("Still needs to be executed: ", not_executed)
        
        # Pick an event to schedule
        for event in enabled:
                # Check that the wait constraints on the event are satisfied
                waits = dc_network.verts[event].outgoing_upper
                lower_bound = time_windows[event][0]
                
                for edge in waits:
                    if edge.parent != event:
                        if (edge.parent not in executed):
                            lower_bound = max(lower_bound, 
                                    schedule[edge.j] - edge.weight)
                
                if lower_bound < min_time:
                    min_time = lower_bound
                    current_event = event


        is_uncontrollable = current_event in uncontrollable_events

        # print("We are scheduling event", current_event, "at time", min_time)
       #  if is_uncontrollable:
            # print("This event is uncontrollable!!!")
        current_time = min_time
        schedule[current_event] = current_time

        # # Check to see if any uncontrollable events should occur before this
        # if not uncontrollable_times.isEmpty():
        #     other_min, event = uncontrollable_times.pop()
        #     if other_min < min_time:
        #         # Update the current event
        #         min_time = other_min
        #         current_event = event
        #         is_uncontrollable = True
        #     else:
        #         # Push it back on the queue
        #         uncontrollable_times.push(event, other_min)

        # If the executed event was a contingent source
        if current_event in contingent_map:
            uncontrollable = contingent_map[current_event]
            delay = realization[uncontrollable]
            set_time = current_time + delay
            # uncontrollable_times.push(uncontrollable, set_time)
            enabled.add(uncontrollable)
            time_windows[uncontrollable] = [set_time, set_time]



        if is_uncontrollable:
            # Remove waits
            original_edges = list(dc_network.upper_case_edges.items())
            for nodes, edge in original_edges:
                if edge.parent == current_event:
                    if (current_event != edge.i) and (current_event != edge.j):
                        # Modifying the network
                        dc_network.remove_upper_edge(edge.i, edge.j)

        not_executed.remove(current_event)
        enabled.remove(current_event)
        executed.add(current_event)

        # Propagate the constraints
        for nodes, edge in dc_network.normal_edges.items():
            if edge.i == current_event:
                # print("Looking at edge", edge)
                new_upper_bound = edge.weight + current_time
                if new_upper_bound < time_windows[edge.j][1]:
                    time_windows[edge.j][1] = new_upper_bound
                    # print(f"Changed to {edge.j}: {time_windows[edge.j]}")
                    # assert new_upper_bound >= time_windows[edge.j][0], \
                    #         f"Incompatible window {edge.j}: {time_windows[edge.j]}"
            if edge.j == current_event:
                # print("Looking at edge", edge)
                new_lower_bound = current_time - edge.weight
                if new_lower_bound > time_windows[edge.i][0]:
                    time_windows[edge.i][0] = new_lower_bound
                    # print(f"Changed to {edge.i}: {time_windows[edge.i]}")
                    # assert new_lower_bound <= time_windows[edge.i][1], \
                    #         f"Incompatible window {edge.i}: {time_windows[edge.i]}."

        # Add newly enabled events
        for event in not_executed:
            if (event not in enabled) and (event not in uncontrollable_events):
                # Check if the event is enabled
               #  print("***")
               #  print(f"Checking if {event} is enabled...")
                ready = True
                outgoing_reqs = dc_network.verts[event].outgoing_normal
                # Check required constraints
                for edge in outgoing_reqs:
                    # For required 
                    if edge.weight < 0:
                    #     print("Need to occur after", edge.j)
                        if edge.j not in executed:
                            ready = False
                            break
                
                # Check wait constraints
                outgoing_upper = dc_network.verts[event].outgoing_upper
                for edge in outgoing_upper:
                    if edge.weight < 0:
                        label_wait = (edge.parent not in executed)
                        main_wait = (edge.j not in executed)
                  #       print("Need to occur after", edge.parent, "and", edge.j)
                        if label_wait and main_wait:
                            ready = False
                            break

                if ready:
                    enabled.add(event)
                # print("***")

    # print("\n\nFinal schedule is: ")
    # print(schedule)
    good = scheduleIsValid(network, schedule), "Invalid!"
    msg = "We're good" if good else "We're dead"
    print(msg)

##
# \fn generate_realization(network)
def generate_realization(network: STN) -> dict:
    realization = {}
    for nodes, edge in network.contingentEdges.items():
        realization[nodes[1]] = random.uniform(-edge.Cji, edge.Cij)
    return realization



def main():
    file_name = "stnudata/dynamic/dynamic112.json"
    # file_name = "test.json"
    network = loadSTNfromJSONfile(file_name)

    simulation(network, 10)

if __name__ == "__main__":
    main()
