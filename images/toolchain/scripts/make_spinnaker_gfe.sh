#!/usr/bin/env bash

set -eu

# Set the compiler install directory
cd spinnaker_tools
set +eu && . ~/.spinnaker_env; set -eu   # source `setup' defined in .spinnaker_env
make clean
make
cd ..

cd spinn_common
make clean
make || exit $?
make install
cd ..

cd SpiNNMan/c_models/reinjector
make
cd ../../..

cd SpiNNFrontEndCommon/c_common/front_end_common_lib
make install-clean
cd ..
make clean
make
make install
cd ../..

cd SpiNNakerGraphFrontEnd/spinnaker_graph_front_end/examples
make clean
make
cd ../../..
