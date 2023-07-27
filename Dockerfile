# Dockerfile

# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

# Install rtl-sdr and multimon-ng dependencies
RUN apt-get update && \
    apt-get install -y \
    git \
    cmake \
    build-essential \
    libusb-1.0-0-dev \
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
COPY pager_telegram_forwarder.py config.txt /app/

# Command to run the application
CMD [ "python", "-u", "pager_telegram_forwarder.py" ]
