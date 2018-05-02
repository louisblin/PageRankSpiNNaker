FROM ubuntu:14.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY config/* /root/

# Install system dependencies
RUN locale-gen en_GB en_GB.UTF-8 && dpkg-reconfigure locales
RUN apt-get update && apt-get upgrade -y

# Install python dependencies
RUN apt-get install -y build-essential python-dev python-setuptools python-tk x11-apps && easy_install pip
# Will install with SSL warnings, to remove them for further downloads
RUN pip install requests[security]
RUN pip install --upgrade setuptools pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Removes errors due to expected interaction
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

# Run test if not used interactively
CMD ["python", "PyNN8Examples/examples/va_benchmark.py"]
