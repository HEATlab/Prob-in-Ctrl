from stn import STN, loadSTNfromJSONfile
from util import STNtoDCSTN, PriorityQueue
from dc_stn import DC_STN
import empirical
import random
import json


# For faster checking, recently added (just for safely_scheduled)
import simulation as sim

##
# \file dispatch.py
# \brief Hosts method to dispatch STNUs that were modified by the
#        old dynamic checking algorithm
# \note More exposition can be found in: 
#       https://pdfs.semanticscholar.org/0313/af826f45d090a63fd5d787c92321666115c8.pd

ZERO_ID = 0
LARGE_NUMBER = 1000000000000000

##
# \fn simulate_and_save(file_names)
# \brief Keep track of dispatch results on networks
def simulate_and_save(file_names: list, size: int, out_name: str):
    rates = {}
    # Loop through files and record the dispatch success rates and 
    # approximated probabilities
    for name in file_names:
        success_rate = simulate_file(name, size)
        rates[name] = success_rate

    # Save the results
    with open(out_name, 'w') as out_json:
        out_json.dump(rates)
    print("Results saved to", out_name)

##
# \fn simulate_file(file_name, size)
def simulate_file(file_name, size, verbose = False) -> float:
    network = loadSTNfromJSONfile(file_name)
    # if verbose:
    #     print("The original network:")
    #     print(network)
    result = simulation(network, size, verbose)
    print(f"{file_name} worked {100*result}% of the time.")

##
# \fn simulation(network, size)
def simulation(network: STN, size: int, verbose = False) -> float:
    # Some data useful from the original network
    contingent_pairs = network.contingentEdges.keys()
    contingents = {src: sink for (src, sink) in contingent_pairs}
    uncontrollables = set(contingents.values())

    total_victories = 0
    dc_network = STNtoDCSTN(network)
    dc_network.addVertex(ZERO_ID)

    controllability = dc_network.is_DC()
    # print("Finished checking DC...")
   
    # If the network has a suspicious life, set it right
    # (looks for inconsistency in one fixed edge)
    ###########
    verts = dc_network.verts.keys()
    for vert in verts: 
        if (vert, vert) in dc_network.edges:
            # print("Checking", vert)
            edge = dc_network.edges[vert, vert][0]
            if edge.weight < 0:
                dc_network.edges[(vert, vert)].remove(edge)
                dc_network.verts[vert].outgoing_normal.remove(edge)
                dc_network.verts[vert].incoming_normal.remove(edge)
                del dc_network.normal_edges[(vert, vert)]
    ###########

    # Running the simulation
    for j in range(size):
        realization = generate_realization(network)
        # print("*******")
        # print("The realization was ")
        # print(realization)
        # print("********")
        copy = dc_network.copy()
        # print("Made the copy.")
        # print("The copy looks like: ")
        # print(copy)
        # print("The original version looks like: ")
        # print(dc_network)
        result = dispatch(network, copy, realization, 
                contingents, uncontrollables, False)
        # print("Completed a simulation.")
        if result:
            total_victories += 1
    
    goodie = float(total_victories/size)
    # print(f"Worked {100*goodie}% of the time.")
    
    # if controllability:
        # print("It's dynamically controllable!")
    # else:
       #  print("It is not dynamically controllable.")
    return goodie

##
# \fn dispatch(network)
def dispatch(network: STN, dc_network: DC_STN, realization: dict, 
        contingent_map: dict, uncontrollable_events, verbose = False) -> bool:

    ## Dispatch the modified network
    # Assume we have a zero reference point
    enabled = {ZERO_ID}
    not_executed = set(dc_network.verts.keys())
    executed = set()
    current_time = 0.0
    
    schedule = {}

    time_windows = {event: [0, float('inf')] for event in not_executed}
    current_event = ZERO_ID
    # print("Beginning dispatch...")
    while len(not_executed) > 0:
        # Find next event to execute
        min_time = float('inf')

        if verbose:
            print("\n\nNetwork looks like: ")
            print(dc_network)

            print("Current time windows: ", time_windows)
            print("Currently enabled: ", enabled)
            print("Already executed: ", executed)
            print("Still needs to be executed: ", not_executed)
        
        # Pick an event to schedule
        for event in enabled:
            lower_bound = time_windows[event][0]
            if event in uncontrollable_events:
                if lower_bound < min_time:
                    min_time = lower_bound
                    current_event = event
            else:
                # Check that the wait constraints on the event are satisfied
                waits = dc_network.verts[event].outgoing_upper
                lower_bound = time_windows[event][0]
                
                for edge in waits:
                    if edge.parent != event:
                        if (edge.parent not in executed):
                            if edge.j not in executed:
                                continue
                            lower_bound = max(lower_bound, 
                                    schedule[edge.j] - edge.weight)
                
                if lower_bound < min_time:
                    min_time = lower_bound
                    current_event = event


        is_uncontrollable = current_event in uncontrollable_events

        if verbose:
            print("We are scheduling event", current_event, "at time", min_time)
            if is_uncontrollable:
                print("This event is uncontrollable!!!")
        current_time = min_time
        schedule[current_event] = current_time

        # Quicker check for scheduling errors
        if not sim.safely_scheduled(network, schedule, current_event):
            if verbose:
                print("Failed -- event", current_event, "violated a constraint.")
                print(f"At this time, we still had {len(not_executed)} " 
                        f"out of {len(dc_network.verts)} events left to schedule")
                verbose = False
            return False

        # If the executed event was a contingent source
        if current_event in contingent_map:
            uncontrollable = contingent_map[current_event]
            delay = realization[uncontrollable]
            set_time = current_time + delay
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
            if verbose:
                print("***")
                print("Checking event", event)
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
                            if verbose:
                                print(event, "was not enabled because of", 
                                        edge)
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
                            if verbose:
                                print(event, "was not enabled because of", edge)
                            break

                if ready:
                    enabled.add(event)
                # print("***")

    # The realization should have been preserved
    # for src, sink in contingent_map:

    if verbose:
        print("\n\nFinal schedule is: ")
        print(schedule)
        print("Network is: ")
        print(network)
    # good = empirical.scheduleIsValid(network, schedule)
    # # msg = "We're good" if good else "We're dead"
    # # print(msg)
    # # print("Schedule was: ")
    # # for k, v in schedule.items():
    # #     # if k == 0:
    # #     if k != -1:
    # #         print(f"Event {k} was assigned time {v}")
    # #     else:
    # #         print(f"Event {k} occurred {v - schedule[k-1]} seconds"
    # #                 f" after event {k-1}.")
    # return good
    return True

##
# \fn generate_realization(network)
def generate_realization(network: STN) -> dict:
    realization = {}
    for nodes, edge in network.contingentEdges.items():
        realization[nodes[1]] = random.uniform(-edge.Cji, edge.Cij)
    return realization


def main():
    ### Testing
    SAMPLE_SIZE = 800
    # rel_path = "stnudata/uncertain/"
    # beg = "uncertain"
    beg = "new_uncertain"
    end = ".json"

    rel_path = "stnudata/more_uncertain/"

    # good_list = list(range(1,32))
    # BAD: 10, 21, 24, 27, 29
    good_list = range(48, 133)
    # bad_set = {10, 21, 24, 27, 29}
    bad_set = set()
    # good_list = [17]

    # good_list = range(1, 48)
    # good_list = [25]
    # bad_set = {17} 
    # file_names = [f"{rel_path}{beg}{j}{end}" for j in good_list if j not in bad_set] 
    file_names = [f"{rel_path}{beg}{j}{end}" for j in good_list if j not in bad_set]

    for name in file_names:
        simulate_file(name, SAMPLE_SIZE, verbose=False)

if __name__ == "__main__":
    main()
