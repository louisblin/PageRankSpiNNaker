# Use an official Python runtime as a parent image
FROM ubuntu:14.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app
ADD .spynnaker.cfg /root/.spynnaker.cfg

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y build-essential python-dev python-setuptools python-tk x11-apps && easy_install pip
# Will install with SSL warnings, to remove them for further downloads
RUN pip install requests[security]
RUN pip install --upgrade setuptools pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Removes errors due to expected interaction
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

# Run app.py when the container launches
CMD ["python", "PyNN8Examples-4.0.0/examples/va_benchmark.py"]
