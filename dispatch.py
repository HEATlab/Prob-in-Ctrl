from stn import STN, loadSTNfromJSONfile
from util import STNtoDCSTN
from dc_stn import DC_STN

##
# \file dispatch.py
# \brief Hosts method to dispatch STNUs that were modified by the
#        old dynamic checking algorithm
# \note More exposition can be found in: 
#       https://pdfs.semanticscholar.org/0313/af826f45d090a63fd5d787c92321666115c8.pd

ZERO_ID = 0

##
# \fn dispatch(network)
def dispatch(network: STN) -> bool:
    ## Turn the STNU into the old class
    dc_network = STNtoDCSTN(network)

    ## Modify the network
    controllability = dc_network.is_DC()

    ## Dispatch the modified network
    # Assume we have a zero reference point
    enabled = {ZERO_ID}
    not_executed = set(dc_network.verts.keys())
    current_time = 0.0

    while 

    return 0
