#!/bin/bash

SPINN_REPOS="
SpiNNakerGraphFrontEnd
SpiNNFrontEndCommon
PACMAN
SpiNNMan
DataSpecification
SpiNNMachine
SpiNNStorageHandlers
spinnaker_tools
spinn_common
ybug
"

for rep in $SPINN_REPOS
do
  git clone "https://github.com/SpiNNakerManchester/$rep.git"
  cd "$rep"
  git fetch --all --tags --prune
  git checkout tags/2016.001 -b v2016-001

  # If python, run setup.py
  if [ -f setup.py ]; then
    sudo python setup.py develop --no-deps
  fi

  cd ..
done

sudo pip install --upgrade enum34 six
sudo pip install "rig <= 1.1.0"
