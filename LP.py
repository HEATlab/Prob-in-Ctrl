from stn import STN
from stn import loadSTNfromJSONfile
from pulp import *
import math
import json

## \file LP.py
#  \brief Convert an input STNU to LP form and computes the degree of
#         controllability


##
#  \fn addConstraint(constraint,problem)
#  \brief Adds an LP constraint to the given LP
#
#  @param constraint A constraint that need to be added to the LP problem
#  @param problem    An input LP problem
#
#  @post LP problem with new constraint added
def addConstraint(constraint,problem):
    problem += constraint


##
# \fn setUp(STN, super=True, two_step=False)
# \brief Initializes the LP problem and the LP variables
#
# @param STN        An input STNU
# @param super      Flag indicating if we want to solve for Superintercal
#                   (strongly controllable) or Max Subinterval(weak/dynamic)
# @param two_step   Flag indicating if we are applying the two step method with
#                   only one universal epsilon
#
# @return   A tuple (bounds, deltas, prob) where bounds and deltas are
#           dictionaries of LP variables, and prob is the LP problem instance
def setUp(STN, super=True, two_step=False):
    bounds = {}
    epsilons = {}

    # Maximize for super and minimize for Subinterval
    if super:
        prob = LpProblem('SuperInterval LP', LpMaximize)
    else:
        prob = LpProblem('Max Subinterval LP', LpMinimize)

    # ##
    # Store Original STN edges and objective variables for easy access.
    # Not part of LP yet
    # ##
    for i in STN.verts:
        bounds[(i,'+')] = LpVariable('t_%i_hi'%i, lowBound=0,
                                            upBound=STN.getEdgeWeight(0,i))

        bounds[(i,'-')] = LpVariable('t_%i_lo'%i,
                                lowBound=-STN.getEdgeWeight(i,0), upBound=None)

        addConstraint( bounds[(i,'-')] <= bounds[(i,'+')], prob)

        if i == 0:
            addConstraint(bounds[(i,'-')] == 0, prob)
            addConstraint(bounds[(i,'+')] == 0, prob)


    # If applying two_step method, only one epsilon is needed
    if two_step:
        epsilons[('eps','-')] = LpVariable('eps', lowBound=0, upBound=None)

    for i,j in STN.edges:
        if (i,j) in STN.contingentEdges:
            if not two_step:
                epsilons[(j,'+')] = LpVariable('eps_%i_hi'%j, lowBound=0,
                                                                upBound=None)
                epsilons[(j,'-')] = LpVariable('eps_%i_lo'%j, lowBound=0,
                                                                upBound=None)

                if super:
                    addConstraint(bounds[(j,'+')]-bounds[(i,'+')] ==
                            STN.getEdgeWeight(i,j) + epsilons[(j,'+')], prob)
                    addConstraint(bounds[(j,'-')]-bounds[(i,'-')] ==
                            -STN.getEdgeWeight(j,i) - epsilons[(j,'-')], prob)

                else:
                    addConstraint(bounds[(j,'+')]-bounds[(i,'+')] ==
                            STN.getEdgeWeight(i,j) - epsilons[(j,'+')], prob)
                    addConstraint(bounds[(j,'-')]-bounds[(i,'-')] ==
                            -STN.getEdgeWeight(j,i) + epsilons[(j,'-')], prob)

            elif super:
                addConstraint(bounds[(j,'+')]-bounds[(i,'+')] ==
                        STN.getEdgeWeight(i,j) + epsilons[('eps','-')], prob)
                addConstraint(bounds[(j,'-')]-bounds[(i,'-')] ==
                        -STN.getEdgeWeight(j,i) - epsilons[('eps','-')], prob)

            else:
                addConstraint(bounds[(j,'+')]-bounds[(i,'+')] ==
                        STN.getEdgeWeight(i,j) - epsilons[('eps','-')], prob)
                addConstraint(bounds[(j,'-')]-bounds[(i,'-')] ==
                        -STN.getEdgeWeight(j,i) + epsilons[('eps','-')], prob)

        else:
            addConstraint(bounds[(j,'+')]-bounds[(i,'-')] <=
                                            STN.getEdgeWeight(i,j), prob)
            addConstraint(bounds[(i,'+')]-bounds[(j,'-')] <=
                                            STN.getEdgeWeight(j,i), prob)

    return (bounds, epsilons, prob)




##
# \fn originalLP(STN, super=True, two_step=False, naiveObj=True, debug=False)
# \brief Runs the LP on the input STN
#
# @param STN        An input STNU
# @param super      Flag indicating if we want to solve for Superintercal
#                   (strongly controllable) or Max Subinterval(weak/dynamic)
# @param two_step   Flag indicating if we are applying the two step method with
#                   only one universal epsilon
# @param naiveObj   Flag indicating if we are using the naive objective function
# @param debug Print optional status messages
#
# @return   A dictionary of the LP_variables for the bounds on timepoints.
def originalLP(STN, super=True, two_step=False, naiveObj=True, debug=False):
    bounds, epsilons, prob = setUp(STN, super=super, two_step=two_step)

    # Set up objective function for the LP
    if naiveObj or (two_step and not naiveObj):
        Obj = sum([epsilons[(i,j)] for i,j in epsilons])
    else:
        eps = []
        for i,j in STN.contingentEdges:
            c = STN.edges[(i,j)].Cij + STN.edges[(i,j)].Cji
            eps.append( (epsilons[(j,'+')]+epsilons[j,'-'])/c )
        Obj = sum(eps)

    prob += Obj, "Maximize the Super-Interval/Max-Subinterval for the input STN"

    # write LP into file for debugging (optional)
    if debug:
        prob.writeLP('original.lp')
        LpSolverDefault.msg = 10

    try:
        prob.solve()
    except Exception:
        print("The LP is infeasible")
        return None

    # Report optional status message
    status = LpStatus[prob.status]
    if debug:
        print("Status: ", status)

        for v in prob.variables():
            print(v.name, '=', v.varValue)

    if status != 'Optimal':
        print("The solution for LP is not optimal")
        return None

    return bounds
