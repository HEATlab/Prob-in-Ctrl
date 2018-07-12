from stn import STN
from stn import loadSTNfromJSONfile
from pulp import *
import math
import json
import glob
import os
import sys


##
# \brief A global variable that stores the max float that will be used to deal
#        with infinite edges.
MAX_FLOAT = sys.float_info.max


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
# \fn setUp(STN, super=True, uniform_step=False)
# \brief Initializes the LP problem and the LP variables
#
# @param STN            An input STNU
# @param super          Flag indicating if we want to solve for Superintercal
#                       (strongly controllable) or Max Subinterval(weak/dynamic)
# @param uniform_step   Flag indicating if we are applying the two step method
#                       with only one universal epsilon
# @param proportion     Flag indicating whether we are setting up LP to
#                       proportionally shrink contingent intervals
# @param maxmin         Flag indicating whether we are setting up LP to
#                       maximize the min shrinked contingent intervals
#
# @return   A tuple (bounds, deltas, prob) where bounds and deltas are
#           dictionaries of LP variables, and prob is the LP problem instance
def setUp(STN, super=True, uniform_step=False, proportion=False, maxmin=False):
    bounds = {}
    epsilons = {}

    # Maximize for super and minimize for Subinterval
    if super or maxmin:
        prob = LpProblem('SuperInterval LP', LpMaximize)
    else:
        prob = LpProblem('Max Subinterval LP', LpMinimize)

    # ##
    # NOTE: Our LP requires each event to occur within a finite interval. If
    #       the input LP does not have finite interval specified for all
    #       events, we want to set the setMakespan to MAX_FLOAT (infinity)
    #       so the LP works
    #
    #       We do not want to run minimal network first because we are going to
    #       modify the contingent edges in LP, while some constraints in
    #       minimal network are obtained through contingent edges
    #
    #       There might be better way to deal with this problem.
    # ##
    for i in STN.verts:
        if STN.getEdgeWeight(0,i) == float('inf'):
            STN.setMakespan(MAX_FLOAT)
            break

    # ##
    # Store Original STN edges and objective variables for easy access.
    # Not part of LP yet
    # ##
    for i in STN.verts:
        bounds[(i,'+')] = LpVariable('t_%i_hi'%i, lowBound=0,
                                            upBound=STN.getEdgeWeight(0,i))

        lowbound = 0 if STN.getEdgeWeight(i,0) == float('inf') else\
                            -STN.getEdgeWeight(i,0)
        bounds[(i,'-')] = LpVariable('t_%i_lo'%i, lowBound=lowbound,
                                                            upBound=None)

        addConstraint( bounds[(i,'-')] <= bounds[(i,'+')], prob)

        if i == 0:
            addConstraint(bounds[(i,'-')] == 0, prob)
            addConstraint(bounds[(i,'+')] == 0, prob)


    if proportion:
        return (bounds, epsilons, prob)


    # If applying uniform_step method, only one epsilon is needed
    if uniform_step:
        upbound = None

        # ##
        # NOTE: If we do not set this bound, the epsilon does not make sense
        #       for one of our examples. Set up this first, maybe change in
        #       the future
        # ##
        if not super:
            intL = [(e.Cij + e.Cji) for e in STN.contingentEdges.values()]
            upbound = min(intL) / 2
        else:
            lowL = [-e.Cji for e in STN.contingentEdges.values()]
            upbound = min(lowL)

        epsilons[('eps','-')] = LpVariable('eps', lowBound=0, upBound=upbound)

    for i,j in STN.edges:
        if (i,j) in STN.contingentEdges:
            if not uniform_step:
                epsilons[(j,'+')] = LpVariable('eps_%i_hi'%j, lowBound=0,
                                                                upBound=None)
                epsilons[(j,'-')] = LpVariable('eps_%i_lo'%j, lowBound=0,
                                                                upBound=None)

                if super:
                    addConstraint(bounds[(j,'+')]-bounds[(i,'+')] ==
                            STN.getEdgeWeight(i,j) + epsilons[(j,'+')], prob)
                    addConstraint(bounds[(j,'-')]-bounds[(i,'-')] ==
                            -STN.getEdgeWeight(j,i) - epsilons[(j,'-')], prob)


                    # ##
                    # NOTE: A contingent interval cannot have negative lower
                    #       bound. This is not an issue for Wilson's LP because
                    #       the Max Subinterval always make the lower bound
                    #       larger. But we need to make sure that we add this
                    #       constraint here.
                    # ##
                    addConstraint(-STN.getEdgeWeight(j,i) -
                                            epsilons[(j,'-')] >= 0, prob)

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
            # NOTE: We need to handle the infinite weight edges. Otherwise
            #       the LP would be infeasible
            upbound = MAX_FLOAT if STN.getEdgeWeight(i,j) == float('inf') \
                                            else STN.getEdgeWeight(i,j)
            lowbound = MAX_FLOAT if STN.getEdgeWeight(j,i) == float('inf') \
                                            else STN.getEdgeWeight(j,i)

            addConstraint(bounds[(j,'+')]-bounds[(i,'-')] <= upbound, prob)
            addConstraint(bounds[(i,'+')]-bounds[(j,'-')] <= lowbound, prob)

    return (bounds, epsilons, prob)




##
# \fn originalLP(STN, super=True, uniform_step=False, naiveObj=True,debug=False)
# \brief Runs the LP on the input STN
#
# @param STN            An input STNU
# @param super          Flag indicating if we want to solve for Superintercal
#                       (strongly controllable) or Max Subinterval(weak/dynamic)
# @param uniform_step   Flag indicating if we are applying the two step method
#                       with only one universal epsilon
# @param naiveObj       Flag indicating if we are using the naive objective
#                       function
# @param debug          Print optional status messages
#
# @return   LP status, A dictionary of the LP_variables for the bounds on
#           timepoints and a dictionary of LP variables for epsilons
def originalLP(STN, super=True, uniform_step=False, naiveObj=True, debug=False):
    bounds, epsilons, prob = setUp(STN, super=super, uniform_step=uniform_step)

    # Set up objective function for the LP
    if naiveObj or (uniform_step and not naiveObj):
        #Obj = sum([epsilons[(i,j)] for i,j in epsilons])
        Obj = epsilons[('eps','-')] if uniform_step \
                            else sum([epsilons[(i,j)] for i,j in epsilons])
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
        print("The model is invalid.")
        return 'Invalid', None, None

    # Report status message
    status = LpStatus[prob.status]
    print("Status: ", status)

    for v in prob.variables():
        print(v.name, '=', v.varValue)

    if status != 'Optimal':
        print("The solution for LP is not optimal")
        return status, None, None

    return status, bounds, epsilons


##
# \fn proportionLP(STN, debug=False)
# \brief Runs the Proportion LP on the input STN
#
# @param STN            An input STNU (should be weakly or dynamically
#                       controllable)
# @param debug          Print optional status messages
#
# @return   LP solving status, Lp variable delta and a dictionary of the
#           LP_variables for epsilons
def proportionLP(STN, debug=False):
    # set up the constraints for every vertex
    bounds, epsilons, prob = setUp(STN, super=False, proportion=True)
    delta = LpVariable('delta', lowBound=0, upBound=1)

    # set up constraints for every edges
    for i,j in STN.edges:
        if (i,j) in STN.contingentEdges:
            epsilons[(j,'+')] = LpVariable('eps_%i_hi'%j, lowBound=0,
                                                            upBound=None)
            epsilons[(j,'-')] = LpVariable('eps_%i_lo'%j, lowBound=0,
                                                            upBound=None)

            addConstraint(bounds[(j,'+')]-bounds[(i,'+')] ==
                    STN.getEdgeWeight(i,j) - epsilons[(j,'+')], prob)
            addConstraint(bounds[(j,'-')]-bounds[(i,'-')] ==
                    -STN.getEdgeWeight(j,i) + epsilons[(j,'-')], prob)

            # the proportion of uncertainty removed is delta
            e = STN.contingentEdges[(i,j)].Cij + STN.contingentEdges[(i,j)].Cji
            addConstraint(epsilons[(j,'-')] + epsilons[(j,'+')] == \
                                                            delta * e, prob)

        else:
            upbound = MAX_FLOAT if STN.getEdgeWeight(i,j) == float('inf') \
                                            else STN.getEdgeWeight(i,j)
            lowbound = MAX_FLOAT if STN.getEdgeWeight(j,i) == float('inf') \
                                            else STN.getEdgeWeight(j,i)

            addConstraint(bounds[(j,'+')]-bounds[(i,'-')] <= upbound, prob)
            addConstraint(bounds[(i,'+')]-bounds[(j,'-')] <= lowbound, prob)

    # The objective of the LP is just to minimize the value of alpha
    Obj = delta
    prob += Obj, "Minimize delta for the input STN"

    # write LP into file for debugging (optional)
    if debug:
        prob.writeLP('proportion.lp')
        LpSolverDefault.msg = 10

    try:
        prob.solve()
    except Exception:
        print("The model is invalid.")
        return 'Invalid', None, None

    # Report status message
    status = LpStatus[prob.status]
    if debug:
        print("Status: ", status)

        for v in prob.variables():
            print(v.name, '=', v.varValue)

    if status != 'Optimal':
        print("The solution for LP is not optimal")
        return status, None, None

    return status, delta, epsilons


##
# \fn maxminLP(STN, debug=False)
# \brief Runs the maximin LP on the input STN, try to maximize the min length
#        of the shrinked contingent interval
#
# @param STN            An input STNU (should be weakly or dynamically
#                       controllable)
# @param debug          Print optional status messages
#
# @return   LP solving status, min contingent int length and a dictionary of the
#           LP_variables for epsilons
def maxminLP(STN, debug=True):
    bounds, epsilons, prob = setUp(STN, super=False, maxmin=True)
    z = LpVariable('z', lowBound=0, upBound=None)

    for (i,j) in STN.contingentEdges:
        c = STN.getEdgeWeight(i,j) + STN.getEdgeWeight(j,i)
        addConstraint(z <= c - epsilons[(j,'-')] - epsilons[(j,'+')], prob)

    # The objective of the LP is just to minimize the value of alpha
    Obj = z
    prob += Obj, "Maximize minimum contingent intervals"

    # write LP into file for debugging (optional)
    if debug:
        prob.writeLP('maxmin.lp')
        LpSolverDefault.msg = 10

    try:
        prob.solve()
    except Exception:
        print("The model is invalid.")
        return 'Invalid', None, None

    # Report status message
    status = LpStatus[prob.status]
    if debug:
        print("Status: ", status)

        for v in prob.variables():
            print(v.name, '=', v.varValue)

    if status != 'Optimal':
        print("The solution for LP is not optimal")
        return status, None, None

    return status, z, epsilons




##
# \fn minmaxLP(STN, debug=False)
# \brief Runs the minmax LP on the input STN, try to minimize the max
#        amount of uncertainty removed from contingent intervals
#
# @param STN            An input STNU (should be weakly or dynamically
#                       controllable)
# @param debug          Print optional status messages
#
# @return   LP solving status, max amount of uncertainty removed from contingent
#           intervals and a dictionary of the LP_variables for epsilons
def minmaxLP(STN, debug=True):
    bounds, epsilons, prob = setUp(STN, super=False)
    z = LpVariable('z', lowBound=0, upBound=None)

    for (i,j) in STN.contingentEdges:
        addConstraint(z >= epsilons[(j,'-')] + epsilons[(j,'+')], prob)

    # The objective of the LP is just to minimize the value of alpha
    Obj = z
    prob += Obj, "Minimize the maximum of uncertainty removed"

    # write LP into file for debugging (optional)
    if debug:
        prob.writeLP('minmax.lp')
        LpSolverDefault.msg = 10

    try:
        prob.solve()
    except Exception:
        print("The model is invalid.")
        return 'Invalid', None, None

    # Report status message
    status = LpStatus[prob.status]
    if debug:
        print("Status: ", status)

        for v in prob.variables():
            print(v.name, '=', v.varValue)

    if status != 'Optimal':
        print("The solution for LP is not optimal")
        return status, None, None

    return status, z, epsilons
