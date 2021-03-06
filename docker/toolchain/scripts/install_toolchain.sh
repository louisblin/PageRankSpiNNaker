#!/usr/bin/env bash

set -eu

function clone_repository {
  rep="$1"
  tag="$2"
  args="${3:-}"

  git clone "https://github.com/SpiNNakerManchester/$rep.git"
  cd "$rep"
  git fetch --all --tags --prune
  git checkout "tags/$tag" -b "v$tag"

  # If python, run setup.py
  if [ -f setup.py ]; then
    sudo python setup.py develop ${args}
  fi

  cd -
}

SPINN_COMMON_REPOS="
SpiNNakerGraphFrontEnd
SpiNNFrontEndCommon
PACMAN
SpiNNMan
DataSpecification
SpiNNMachine
SpiNNStorageHandlers
spinn_common
"

sudo pip install --upgrade enum34 six wheel setuptools pip jsonschema "requests>=2.4.1"


case $DOCKER_TAG in
    v2016.001)   ### DOCKER_TAG=2016.001
    sudo pip install "rig <= 1.1.0"

    for rep in $SPINN_COMMON_REPOS; do
        clone_repository "$rep" "2016.001" "--no-deps"
    done
    clone_repository "spalloc"         "v0.2.6"
    clone_repository "spinnaker_tools" "2016.001" "--no-deps"
    clone_repository "ybug"            "2016.001" "--no-deps"
    ;;

    v4.0.0)      ### DOCKER_TAG=4.0.0
    sudo pip install --user rig appdirs matplotlib "scipy>=0.16.0"

    for rep in $SPINN_COMMON_REPOS; do
        clone_repository "$rep" "4.0.0" "--no-deps"
    done
    clone_repository "SpiNNUtils"      "4.0.0"  "--no-deps"
    clone_repository "spalloc"         "1.0.0"
    clone_repository "spinnaker_tools" "v3.1.1" "--no-deps"
    clone_repository "sPyNNaker"       "4.0.0"  "--no-deps"
    clone_repository "sPyNNaker8"      "4.0.0"
    ;;

    *)          ### unknown DOCKER_TAG
    echo "Unknown DOCKER_TAG=$DOCKER_TAG... abort."; exit 1
    ;;
esac
