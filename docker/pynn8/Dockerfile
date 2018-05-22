# Written for a build context as docker/
FROM ubuntu:14.04

# Set cwd / env
WORKDIR /app
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

# Install config files
COPY pynn8 /app
COPY common/config/* pynn8/config/* /root/

# Install system dependencies
RUN locale-gen en_US en_US.UTF-8 && dpkg-reconfigure locales
RUN apt-get update && apt-get upgrade -y

# Install python dependencies
RUN apt-get install -y build-essential python-dev python-setuptools python-tk x11-apps && easy_install pip
# Will install with SSL warnings, to remove them for further downloads
RUN pip install requests[security]
RUN pip install --upgrade setuptools pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# To be ran interactively
CMD ["/usr/bin/env", "bash"]
