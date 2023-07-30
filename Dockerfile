# Dockerfile

# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libusb-1.0-0-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and build rtl-sdr
RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    cd rtl-sdr && \
    git checkout 0.6.0 && \
    mkdir build && \
    cd build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && \
    make install && \
    ldconfig

# Clone and build multimon-ng
RUN apt-get update && apt-get install -y \
    qt4-qmake \
    libpulse-dev \
    libx11-dev && \
    rm -rf /var/lib/apt/lists/* && \
    git clone https://github.com/EliasOenal/multimon-ng.git && \
    mkdir multimon-ng/build && \
    cd multimon-ng/build && \
    qmake ../multimon-ng.pro PREFIX=/usr/local && \
    make && \
    make install

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY app.py config.txt /app/

# Command to run the application
CMD [ "python", "-u", "app.py" ]
