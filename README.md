# Prob-in-Ctrl
This repository contains a collection of programs written by team *Probably in Control* (part of the Summer 2018 HEATlab group). 
These files were migrated from the repository for Robotbrunch, and earlier group in HEATlab.
The programs here serve to
- generate STNUs, both randomly and from provided PSTN datasets
- compute metrics related to controllability on STNUs
- simulate dispatch on STNUs


## Documentation
Currently, no doxygen.config file exists in this repository.
However, the files are commented so that doxygen documentation can be automatically generated once a config and mainpage files are set up.

## Project Structure
The `stn` folder contains files describing an STN class (which is really a class for STNUs, and more generally could be easily extended to represetn PSTNs) and converting between the class and JSON representations of networks.
The remaining programs are not organized in any particular way. Because of this, in the comments that follow we often describe as a function taking in an "STN" when it really also works with STNUs as input.

### Primary Programs

#### algorithm.py
Implements algorithms for checking if a network is dynamically controllable (DC).
If the network is not DC, there are functions for reporting the "conflicts" that prevent the network from achieving controllability.
##### Details 
Implements the `DCDijkstra` algorithm described in [(Williams 2017)](https://www.ijcai.org/proceedings/2017/598).

#### dispatch.py
Implements a dispatch strategy and associated simulation for STNUs, based off Algorithm 2 from [(Nilsson)](https://pdfs.semanticscholar.org/0313/af826f45d090a63fd5d787c92321666115c8.pdf).
##### Details
This strategy should always succeed for dynamically controllable STNUs.
It works by first leveraging a conversion to the `DC_STN` class to infer wait constraints, and then following early execution.

#### LP.py
Uses `PuLP` module to set up and solve several different LPs.
These LPs are primarily attempts at linearizing the calculation for degree of strong controllability. 
The main structure of the constraints remains the same accross most of the programs, but there are many different types of objective functions used.

#### probability.py
Stores functions that, given conflicts from non-DC network, return the predicted probability of successful dispatch on those networks.
##### Details
The approximation here is an application of CLT to sums of uniformly distributed random variables. 

#### relax.py
Using the routines from `algorithm.py` and `LP.py`, defines various different ways of selecting "maximal" subintervals.
##### Description
The approaches for computing subintervals in the strong controllability case involve using solutiosn from some LPs.
In the dynamic controllability case, the main approach implemented is the `optimalRelax` function, which is a very straightforward algorithm (with `O(k\log k)` complexity, if `k` is the number of edges in the conflict) that finds the true maximum subintervals (in the sense of maximizing resulting volume while ensuring the conflict is resolved).

#### stn/stn.py
Defines STN, Edge, and Vertex classes.
##### Details
A Vertex represents an event in an STN. 
It is encoded as a single node with a unique integer ID.

An Edge represents a constraint in an STN.
It is encoded as a pair of vertex IDs labeled with an interval and type.
The type designates an edge as a requirement (`stc`) or contingnet (`stcu`) edge.

An STN consists of events with constraints in between events. 
An STN object is encoded as set of Vertices with Edges between some pairs of vertices.

In general, a Vertex with ID zero is treated as the zero-timepoint. 

#### stn/stnjsontools.py
Provides functions to create STN objects from input JSON files.


### Secondary Programs

#### dc_stn.py
An older file.
Builds a `DC_STN` class that represents STNUs with an aim of manipulating the associated labeled distance graph. 
Implements the DC checking algorithm described in [(Morris 2003)](https://pdfs.semanticscholar.org/6fb1/b64231b23924bd9e2a1c49f3b282a99e2f15.pdf).
Also has a function for checking if STNs are consistent or not. 

#### empirical.py
Computes and plots empirical results, mainly related to strong controllability.
##### Details
Leverages functions from `LP.py`, `dispatch.py`, and `relax.py` to measure approximate and exact degrees of strong controllability, approximate degrees of dynamic controllability, and true success rates with different dispatch strategies. 
Comtains some methods for plotting these results as well. 

#### empirical_dynamic.py
Computes and stores data for success rates of dynamic dispatch and probabilistic estimates of those success rates.
##### Details
This program generated `result_dynamic.json`.

#### plot.py
A file that makes use of the `plotly` module to make some nice graphs of the results outputted by `empirical.py`.  

#### result_stats.py
A short file for computing correlations between some of the sets of data stored in the `result` folder.

#### simulation.py
Attempts at writing early and late strategies for dispatch on STNUs.
This program did not really end up getting used, since the attempts at implementing early and late strategies here are incorrect.
Instead, we only used the simulation presented in `dispatch.py`.

#### util.py
Holds a few helpful functions, which are called by other programs.
##### Details
Provides
- `STNtoDCSTN`: a function for converting from `STN` objects to `DC_STN` objects
- `normal`:     a function for getting STNUs in normal form (that is, all contingent edges have lower bound zero)
- `PriorityQueue`: a class implementing a standard min-heap

### Interfacing with NEOS

#### build_xml.py
A python program to take in AMPL model files and convert them to an XML format that can be submitted to the NEOS server. 

#### model.py
Given an STNU, builds the corresponding optimization problem for computing the degree of strong controllability for the network.
##### Details
The output is an AMPL file. 
The objective function is the logarithm of the product of the lengths of contingent subintervals. 

#### NeosClient.py
A NEOS Python client (made available by the [NEOS server](https://neos-server.org/neos/downloads.html)) that has been mildly modified. This is used to submit optimization problems to NEOS, and then extract the values achieved by the objective function once the jobs are finished. 



### Other Files

#### result
This folder contains several JSON files storing results we found related to degree of controllability, empirical success rates for dispatch, and solutions to nonlinear optimization problems. 

## Credits
The Summer 2018 HEATlab consisted of teams *Probably in Control*, *Acrobotics*, and *Robot Luncheon*.
The former two are the spiritual successors to the 2017 HEATlab *Polybots* team, while the latter is the evolution and extension of 2017 HEATlab team *Robot Brunch*.
All teams worked at Harvey Mudd College under the supervision of [Professor Jim Boerkoel](https://www.cs.hmc.edu/~boerkoel/) as part of the HMC CS department's "[summer of CS](https://www.cs.hmc.edu/research/)".

- *Probably in Control* ~ Team {Maggie Li, Savana Ammons, Shyan Akmal}
  - Explored the geometry of STNUs and degrees of controllability
- *Acrobotics* ~ Team VivaJoon OjhaLee
  - Explored the durability of schedules in STNs and developed sumobot mascots
- *Robot Luncheon* ~ Senior lab member Jordan R. Abrahams
  - Designed and tested the DREAM algorithm for PSTN dispatch
