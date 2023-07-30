# Dockerfile

# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

# Install rtl-sdr, multimon-ng dependencies, and other necessary packages
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libusb-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone and build rtl-sdr
RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    mkdir rtl-sdr/build && \
    cd rtl-sdr/build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && \
    make install && \
    ldconfig

# Clone and build multimon-ng
RUN git clone https://github.com/EliasOenal/multimon-ng.git && \
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
