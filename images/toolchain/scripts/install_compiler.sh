#!/usr/bin/env bash

COMPILER_DIR="gcc-arm-none-eabi"


case $DOCKER_TAG in
    v2016.001)   ### DOCKER_TAG=2016.001
    DOWNLOAD_URL="https://github.com/SpiNNakerManchester/SpiNNakerManchester.github.io/releases/download/v1.0-lin-dev/arm-2013.05.tgz"
    OUTPUT_DOCUMENT="$COMPILER_DIR.tgz"
    ;;

    v4.0.0)      ### DOCKER_TAG=4.0.0
    DOWNLOAD_URL="https://launchpad.net/gcc-arm-embedded/4.9/4.9-2015-q3-update/+download/gcc-arm-none-eabi-4_9-2015q3-20150921-linux.tar.bz2"
    OUTPUT_DOCUMENT="$COMPILER_DIR.tar.bz2"
    ;;

    *)           ### unknown DOCKER_TAG
    echo "Unknown DOCKER_TAG=$DOCKER_TAG... abort."; exit 1
    ;;
esac

wget -nv "$DOWNLOAD_URL" --output-document "$OUTPUT_DOCUMENT"
mkdir -p "$COMPILER_DIR"
tar -xf "$OUTPUT_DOCUMENT" -C "$COMPILER_DIR"  --strip-components 1
rm -f "$OUTPUT_DOCUMENT"
