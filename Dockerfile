# Use an official Python runtime as a parent image
#FROM python:2.7
#FROM python:2.7-slim
FROM ubuntu:14.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app
ADD .spynnaker.cfg /root/.spynnaker.cfg

# Install any needed packages specified in requirements.txt
RUN sudo apt-get update && sudo apt-get upgrade -y
RUN sudo apt-get install -y build-essential python-dev python-setuptools python-tk x11-apps && sudo easy_install pip
RUN sudo pip install -U setuptools pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Removes errors due to expected interaction
ENV DEBIAN_FRONTEND noninteractive
ENV DISPLAY :0

# Run app.py when the container launches
CMD ["python", "PyNN8Examples-4.0.0/examples/va_benchmark.py"]
