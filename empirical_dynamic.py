##
# \file empirical_dynamic.py
# \brief Computes and saves data for empirically testing how well we can estimate
#        the success of dynamic dispatch rate.
# \note All the data is manually entered in

def save_data():
    # This dictionary has
    # - keys:   names of files
    # - values: (expected success rate, actual success rates)
    dynamic_data = {}

    ## Setup for the files to use
    # File number 22 has strange dispatch error, and is thus omitted
    old_nums = [j for j in range(1, 32) if j != 22]
    # File 17, 21, 25 through 47 had dispatch errors and are omitted
    bad_set = {17, 21}
    new_nums = [j for j in range(1,25) if j not in bad_set]
    
    # This dictionary has
    # - keys: names of folders
    # - values: (base name, list of file nums) 
    paths = {"stnudata/uncertain/": ("uncertain", old_nums), 
            "stnudata/more_uncertain": ("new_uncertain", new_nums)}

    # For now this is hardcoded in. If a function to compute  probabilities in the
    # case of multiple conflicts is computed, this can be replaced.
    UNCERTAIN_12_PROB = 0.14690255486251502

    # How many times we dispatch on each network
    SAMPLE_SIZE = 50000
    
    
    
    return True
