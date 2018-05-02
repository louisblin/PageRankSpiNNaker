FROM ubuntu:14.04

# Set the working directory to /app
WORKDIR /app

# Removes errors due to expected interaction
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

# Copy the current directory contents into the container at /app
COPY . /app
COPY config/* /root/

# Install system dependencies
RUN locale-gen en_GB en_GB.UTF-8 && dpkg-reconfigure locales
RUN apt-get update && apt-get upgrade -y

# Spinnaker toolchain install
RUN apt-get install -y python2.7 python-numpy python-scipy python-lxml python-pip python-tk x11-apps git wget
RUN cd /app && ./scripts/install_toolchain.sh ; cd -

RUN apt-get install -y libc6-i386 perl perl-tk libterm-readline-gnu-perl
RUN cd /app && ./scripts/install_compiler.sh ; cd -

# Set env
ENV SPINN_DIRS /app/spinnaker_tools
ENV PATH $PATH:/app/arm-2013.05/bin:/app/ybug

# Make install
RUN cd /app && ./scripts/make_spinnaker_gfe.sh ; cd -

WORKDIR /app/w
CMD ["python", "-m", "spinnaker_graph_front_end.examples.hello_world.hello_world"]
