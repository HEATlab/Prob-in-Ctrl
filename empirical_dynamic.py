import probability
import dispatch

import json
##
# \file empirical_dynamic.py
# \brief Computes and saves data for empirically testing how well we can estimate
#        the success of dynamic dispatch rate.
# \note All the data is manually entered in

def save_data():
    out_name = "result/result_dynamic.json"
    # This dictionary has
    # - keys:   names of files
    # - values: (expected success rate, actual success rates)
    dynamic_data = {}

    ## Setup for the files to use
    # File number 22 has strange dispatch error, and is thus omitted
    old_nums = [j for j in range(1, 32) if j != 22]
    # File 17, 21, 25 through 47 had dispatch errors and are omitted
    bad_set = {17, 21}.union(set(range(25, 48)), set(range(118, 133)), 
            {52, 58, 62, 70, 72, 80, 81, 85, 94, 104, 116})
    new_nums = [j for j in range(1,139) if j not in bad_set]
    
    # This dictionary has
    # - keys:   names of folders
    # - values: (base name, list of file nums) 
    paths = {"stnudata/uncertain/": ("uncertain", old_nums), 
            "stnudata/more_uncertain/": ("new_uncertain", new_nums)}

    end = ".json"

    # How many times we dispatch on each network
    SAMPLE_SIZE = 800

    for path, info in paths.items():
        beg, file_nos = info

        # Go through the relevant files and store the probability and dispatch rate information
        for j in file_nos:
            file_name = f"{path}{beg}{j}{end}"
            print(f"Testing {beg}{j}{end}.....")

            # Compute probability
            print("Getting probability...")
            expected_success = probability.prob_of_DC_file(file_name)

            # Compute dispatch rate
            print("Getting dispatch rate...")
            observed_success = dispatch.simulate_file(file_name, SAMPLE_SIZE, verbose=False)

            dynamic_data[f"{beg}{j}{end}"] = (expected_success, observed_success)

    # Store the data
    with open(out_name, 'w') as out_file:
        json.dump(dynamic_data, out_file)

    print("Finished storing data.")
    print("Third time's the charm.")

def main():
    save_data()

if __name__ == "__main__":
    main()
