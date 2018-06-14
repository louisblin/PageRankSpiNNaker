# FYP

Final Year Project investigating alternative applications of the SpiNNaker 
hardware. Currently, the focus is on graph based algorithms such as Page Rank.

## Tooling w/ Docker images

[![Build Status](https://travis-ci.com/louisblin/FYP.svg?token=5ZNW4DKhuozscA1A9CAy&branch=master)](https://travis-ci.com/louisblin/FYP)

We build the following docker images to facilitate the development w/ sPyNNaker:

- [**louisleblin/pynn8**](https://hub.docker.com/r/louisleblin/pynn8/):
environment to run the PyNN 0.8 interface to sPyNNaker
- [**louisleblin/toolchain:v2016.001**](https://hub.docker.com/r/louisleblin/toolchain-v2016/):
environment for SpiNNaker Graph Front End Developer toolchain v2016.001
- [**louisleblin/toolchain:v4.0.0**](https://hub.docker.com/r/louisleblin/toolchain-v2016/):
same, but v4.0.0

These images are available under the two versions, accessible via a specific tag:

- **prod** version, via _`<img>`_ for the slim version of the image
- **dev** version, via _`<img>:[<tag>-]dev`_ which adds some development tools such as
`vim` and loads a custom `zsh` / `oh-my-zsh` shell - see
`docker/common/Dockerfile-dev` for further details.

##### Usage

The toolchain v4.0.0 w/ the directory of examples mounted can be started as follows:

```sh
./scripts/start_container louisleblin/toolchain:v4.0.0-dev --volume $PWD/python:/app/w
```

##### Developing

Consider sourcing `./scripts/set_env` in your `.<shell>rc` to add the scripts to your `PATH`. 


## Examples

All the examples are located under `python/page_rank/examples`.

### Page Rank Model (`python/page_rank/model`)

This is a new neuron model that extends those defined by `SpiNNakerManchester/sPyNNaker`. It aims to
 provide an interface to run Page Rank algorithms on top the PyNN neural simulations framework, 
 which sPyNNaker implements. 

To run an `python/page_rank/examples/<example_name>.py`, use:

```sh
# Starts the toolchain container in interactive mode
./scripts/start_container louisleblin/toolchain:v4.0.0-dev --volume $PWD/python:/app/w

...

# In the container
cd page_rank/examples
make <example_name>
```

or as a one-liner:

```sh
./scripts/start_container louisleblin/toolchain:v4.0.0-dev --volume $PWD/python:/app/w --rm --exec "make -C page_rank/examples <example_name>"
```

##### Page Rank on [`simple_4_vertices`](python/page_rank/examples/simple_4_vertices.py)

The following caption shows how the `toolchain:v4.0.0-dev` can be used to compute Page Rank on a 
simple graph as described in [this video](https://www.youtube.com/watch?v=P8Kt6Abq_rM). First, the
input graph is displayed to visually confirm its structure. Then, Page Rank is computed on SpiNNaker
and an output graph is displayed, showing the evolution over time of the rank of each node.

Additionnally, a python implementation of Page Rank runs on the same graph and is used to ensure
the results obtained are correct. As we can see, the results match when comparing the first
three decimals but they differ after that because of fixed point arithmetic imprecision.

_Note_: due to non-deterministic callback scheduling on SpiNNaker, a Page Rank iteration can require
two SpiNNaker time steps to be completed. This leads to duplicate consecutive values on the output
graph.

![Simple Page Rank](docs/page_rank_simple.gif)

