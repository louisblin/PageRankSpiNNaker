# FYP

Final Year Project w/ SpiNNaker hardware

## Docker images

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

## Usage

The toolchain v4.0.0 w/ the directory of examples mounted can be started as follows:

```sh
./scripts/start_container louisleblin/toolchain:v4.0.0-dev --volume $PWD/python:/app/w
```

##### developing

Consider sourcing `./scripts/set_env` in your `.<shell>rc` to add the scripts to your `PATH`. 


## Example

All the examples are located under `python/`.

##### Page Rank [`python/PageRankModel`](https://github.com/louisblin/PageRankModel)

This is a new neuron model that extends those defined by `SpiNNakerManchester/sPyNNaker`. It aims to
 provide an interface to run Page Rank algorithms on top the PyNN neural simulations framework, 
 which sPyNNaker implements. 

The following caption shows how the `toolchain:v4.0.0` can be used to compute Page Rank on a simple 
graph as described in [this video](https://www.youtube.com/watch?v=P8Kt6Abq_rM). First, the input
graph is displayed, where 0 maps to node A, 1 to node B, etc... Then Page Rank is computed on 
SpiNNaker and an output graph is displayed, showing the evolution over time of the rank of each node. 
As we can see, the first three iterations match the results obtained in the video. 

Note: due to non-deterministic callback scheduling on SpiNNaker, duplicate rows can be observed in 
the output and reflect that 2 time steps were required to compute a single Page Rank iteration.

![Simple Page Rank](docs/page_rank_simple.gif)
