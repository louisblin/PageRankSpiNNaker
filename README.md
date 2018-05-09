# FYP

Final Year Project w/ SpiNNaker hardware

## Docker images

[![Build Status](https://travis-ci.com/louisblin/FYP.svg?token=5ZNW4DKhuozscA1A9CAy&branch=master)](https://travis-ci.com/louisblin/FYP)

We build the following docker images to facilitate the development w/ sPyNNaker:

- [**louisleblin/pynn8**](https://hub.docker.com/r/louisleblin/pynn8/):
environment to run the PyNN 0.8 interface to sPyNNaker
- [**louisleblin/toolchain-v2016**](https://hub.docker.com/r/louisleblin/toolchain-v2016/):
environment for SpiNNaker Graph Front End Developer toolchain v2016.001

These images are available under the two versions, accessible via a specific tag:

- **prod** version, via _`<img>`_ for the slim version of the image
- **dev** version, via _`<img>:dev`_ which adds some development tools such as
`vim` and loads a custom `zsh` / `oh-my-zsh` shell - see
`images/common/Dockerfile-dev` for further details.

## Usage

The toolchain v2016.001 w/ the directory of examples mounted can be started as follows:

```sh
./scripts/start_container louisleblin/toolchain-v2016:dev --volume $PWD/examples:/app/w
```

##### developing

Consider sourcing `./scripts/set_env` in your `.<shell>rc` to add the scripts to your `PATH`. 