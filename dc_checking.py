from stn import STN
from stn import loadSTNfromJSONfile
from dc_stn import DC_STN, edgeType

##
# \file dc_checking.py
# \brief Check whether an input STNU is dynamically controllable

##
# \fn STNtoDCSTN(S)
# \brief Convert an STN object to a DC_STN object
#
# @param S  An input STN object to convert
#
# @return A DC_STN object that has the same vertices and edges as the input
def STNtoDCSTN(S):
    new_STN = DC_STN()
    for edge in list(S.edges.values()):
        new_STN.addEdge(edge.i,edge.j,edge.Cij)
        new_STN.addEdge(edge.j,edge.i,edge.Cji)
        if edge.isContingent():
            new_STN.addEdge(edge.i,edge.j,-edge.Cji,edge_type=edgeType.LOWER,parent=edge.j)
            new_STN.addEdge(edge.j,edge.i,-edge.Cij,edge_type=edgeType.UPPER,parent=edge.j)
    return new_STN



##
# \fn dc_checking(STN)
# \brief Check if an input STN is dynamically controllable
#
# @param S  An input STN object to check
#
# @return Return True if the input STN is dynamically controllable. Return
#         False otherwise.
def dc_checking(STN):
    return STNtoDCSTN(STN).is_DC()



##
# \fn dc_checking(filename)
# \brief Check if an input STN is dynamically controllable
#
# @param filename  An input STN object to check
#
# @return Return True if the input STN is dynamically controllable. Return
#         False otherwise.
def dc_checking_file(filename):
    STN = loadSTNfromJSONfile(filename)
    return dc_checking(STN)
