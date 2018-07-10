# Page Rank on SpiNNaker

[![Build Status](https://travis-ci.com/louisblin/PageRankSpiNNaker.svg?branch=master)](https://travis-ci.com/louisblin/PageRankSpiNNaker)

Master's Thesis project at Imperial College London investigating alternative 
applications for the SpiNNaker neuromorphic hardware. The aim is to demonstrate
that the machine offers better scaling opportunities for stateful and massively-
parallel algorithms, such as Page Rank.


This repository constitutes the main contribution of the project, with a 
simulation framework to seamlessly run Page Rank computations on SpiNNaker.

Presentation slides available 
[here](https://www.slideshare.net/LouisBlin/page-rank-on-spinnaker).

## Project structure

```
.
├── docker             // Tools as Docker images
├── python             // Source root
│   └── page_rank      // Python namespacing
│       ├── examples   // User code
│       ├── model      // Framework implementation
│       │   ├── Makefile          // Builds project 
│       │   ├── c_models          // C - Execution on SpiNNaker
│       │   ├── python_models     // Python - Neuron model specification
│       │   ├── requirements.txt
│       │   └── tools             // Python - High-level Page Rank specification 
│       └── tests      // Testing framework code
└── scripts            // Docker / runners utilities 
```


## Tooling w/ Docker images

Environment management is complex for this project so the following Docker 
images were built to ease development w/ SpiNNaker:

- [**louisleblin/pynn8**](https://hub.docker.com/r/louisleblin/pynn8/): user
 install of sPyNNaker8 - to run spiking neural network simulations.
- [**louisleblin/toolchain:v4.0.0**](https://hub.docker.com/r/louisleblin/toolchain-v2016/): developer install of the version 4.0.0 
of the development toolchain - to develop the Page Rank framework.
- [**louisleblin/toolchain:v2016.001**](https://hub.docker.com/r/louisleblin/toolchain-v2016/): same w/ version 2016.001 - to run older
 tutorials based on this version.

These three images are available under the two releases, accessible via a 
specific tag:

- **prod** version, via _`<img>`_ for the slim release of the image
- **dev** version, via _`<img>:[<tag>-]dev`_ which adds some development tools 
such as
`vim` and loads a custom `zsh` / `oh-my-zsh` shell - see
`docker/common/Dockerfile-dev` for further details.

##### Usage

The toolchain v4.0.0 w/ the directory of examples mounted can be started as 
follows:

```sh
./scripts/start_container louisleblin/toolchain:v4.0.0-dev --volume $PWD/python:/app/w
```

Consider modifying `./scripts/start_container` on:
-   network config to interface with SpiNNaker
-   X11 to display graphics from the container over SSH   

##### Developing

Consider sourcing `./scripts/set_env` in your `.<shell>rc` to add the scripts 
to your `PATH`. 


## Page Rank on SpiNNaker

### Page Rank Model (`python/page_rank/model`)

We adapt the existing [`SpiNNakerManchester/sPyNNaker`](https://github.com/SpiNNakerManchester/sPyNNaker) spiking neural network 
framework to support Page Rank simulations. Neurons become vertices, synapses 
are now message dispatchers that propagate rank updates along edges. The model 
is constituted of:

* `c_models`: the C implementation of the model, which runs on SpiNNaker.
* `python_models`: the Python specification of a Page Rank simulation.
* `tools/simulation.py`: a unique interface that exposes a user-friendly
 `PageRankSimulation` class that does all the heavy lifting. 
 
### Examples (`python/page_rank/examples`)

To run an `python/page_rank/examples/<example_name>.py`, use:

```sh
# Starts the toolchain container in interactive mode
./scripts/start_container \
    louisleblin/toolchain:v4.0.0-dev \
    --volume $PWD/python:/app/w

...

# In the container
cd page_rank/examples
make <example_name>
```

or as a one-liner:

```sh
./scripts/start_container \
    louisleblin/toolchain:v4.0.0-dev \
    --volume $PWD/python:/app/w --rm \
    --exec "make -C page_rank/examples <example_name>"
```

##### Minimal example w/ [`simple_4_vertices`](python/page_rank/examples/simple_4_vertices.py)

Command:

```sh
./scripts/start_container \
    louisleblin/toolchain:v4.0.0-dev \
    --volume $PWD/python:/app/w --rm \
    --exec "make -C page_rank/examples simple_4_vertices --show-in --show-out"
```

The following caption shows how the `toolchain:v4.0.0-dev` can be used to 
compute Page Rank on a simple graph as described in 
[this video](https://www.youtube.com/watch?v=P8Kt6Abq_rM). First, the input 
graph is displayed to visually confirm its structure. Then, Page Rank is 
computed on SpiNNaker and an output graph is displayed, showing the evolution 
over time of the rank of each node.

Additionally, a Python implementation of Page Rank runs on the same graph and 
is used to ensure the results obtained are correct.

![Simple Page Rank](docs/page_rank_simple.gif)

