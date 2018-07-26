import json
from scipy.stats.stats import pearsonr

##
# \file result_stats.py
# \brief Collect some statistics related to success rate & accuracy of approximation
#        for DSC in STNUs
# \note Currently computes nothing.


##
# \fn correlation_from_file(data)
# \brief Gets correlation from JSON file with particular format
# 
# @param file_name      The name of the data file
# @return               The correlation and p-value of the input data
def correlation_from_file(file_name: str) -> tuple:
    with open(file_name) as data_file:
        data = json.load(data_file)
    return correlation_of_dict(data)

##
# \fn correlation_of_dict(data) 
# \brief Given a dictionary from data IDs to [x, y] pairs, computes the 
#        correlation of the associated r.v.s X and Y
# 
# @param data      A dictionary storing data points
# @return          The correlation and p-value of the input data
def correlation_of_dict(data: dict) -> tuple:
    data_pts = data.values()
    x_pts = []
    y_pts = []
    
    for pt in data_pts:
        x_pts.append(pt[0])
        y_pts.append(pt[1])
    
    return pearsonr(x_pts, y_pts)

##
# \fn main()
# \brief Takes in json dictionary of data and writes out some statistics.  
def main():
    relpath = "result/"
    fnames = ['result_success.json', 'result_compare.json']
    
    pretty_out = 'pretty_results.txt'
    raw_out = 'stats.json'

    stats = {}
    for file_name in fnames:
        stats[file_name] = correlation_from_file(f"{relpath}{file_name}")

    # For now we just print out the results instead of actually storing them in a file
    for file_nam, stat in stats.items():
        print("The data in", file_name, "had\n\tCorrelation:\t", stat[0], 
                "\n\tP-value:\t", stat[1])
    return 0

if __name__ == '__main__':
    main()
