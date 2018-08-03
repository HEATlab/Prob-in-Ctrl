# Prob-in-Ctrl
This repository contains a collection of programs written by team *Probably in Control* (part of the Summer 2018 HEATlab group). 
These files were migrated from the repository for Robotbrunch, and earlier group in HEATlab.
The programs here serve to
- generate STNUs, both randomly and from provided PSTN datasets
- compute metrics related to controllability on STNUs
- simulate dispatch on STNUs


## (Lack of) Documentation
Currently, no doxygen.config file exists in this repository.
However, the files are commented so that doxygen documentation can be automatically generated once a config and mainpage files are set up.

## Project Structure
The `stn` folder contains files describing an STN class (which is really a class for STNUs, and more generally could be easily extended to represetn PSTNs) and converting between the class and JSON representations of networks.

### Primary Programs

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

#### 


### Secondary Programs

### Other Files

## References

## Credits
