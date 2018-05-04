# Written for a build context as images/
FROM ubuntu:14.04

# Set cwd / env
WORKDIR /app
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

# Copy the current directory contents into the container at /app
COPY toolchain-v2016 /app
COPY common/config/* toolchain-v2016/config/* /root/

# Install system dependencies
RUN locale-gen en_US en_US.UTF-8 && dpkg-reconfigure locales
RUN apt-get update && apt-get upgrade -y

# Spinnaker toolchain install
RUN apt-get install -y python2.7 python-numpy python-scipy python-lxml python-pip python-tk x11-apps git wget
RUN ./scripts/install_toolchain.sh

RUN apt-get install -y libc6-i386 perl perl-tk libterm-readline-gnu-perl
RUN ./scripts/install_compiler.sh

# Set SpiNNaker env
ENV SPINN_DIRS /app/spinnaker_tools
ENV PATH $PATH:/app/arm-2013.05/bin:/app/ybug

# Make install
RUN ./scripts/make_spinnaker_gfe.sh

# To be ran interactively
WORKDIR /app/w
CMD ["/usr/bin/env", "bash"]
