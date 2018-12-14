# Scrubj
## A collection of scripts that utlimately import C functions to Neo4j

This repository is collection of scripts, that import every function in someone's
C code as a node (a.k.a. vertex) in a graph database, in this case Neo4j.
Every function call is represented as an edge. Once the compilation process is
finished, there should be a represantation of the call graph in the database.

The purpose is to be able to query someone's code and possibly discover patterns
or attain a greater understanding of it.

## How to Use

All scripts are in Python 3. There a some dependencies:

[gcc-python-plugin](https://gcc-python-plugin.readthedocs.io/en/latest/basics.html#building-the-plugin-from-source)
Select the branch that is correct for the gcc version you have installed.

[pyzmq](http://zeromq.org/bindings:python)

Make sure the you build the gcc python plugin correctly and set
LD_LIBRARY_PATH=(yourpath)/gcc-python-plugin/gcc-c-api/

Also check out the usage of the [gcc-python-plugin](https://gcc-python-plugin.readthedocs.io/en/latest/basics.html#basic-usage-of-the-plugin).

You'll also need a Neo4j database instance and the abillity to connect to it via
a bolt connection.

The first step is to create a directory named feeds in `/tmp`
Then execute `receiver.py`. The receiver will standby until there is a gcc
compilation.
Use gcc as you would normally, just add the parameters indicated in the
gcc-python-plugin basic usage above.

**This project works only with gcc.**
