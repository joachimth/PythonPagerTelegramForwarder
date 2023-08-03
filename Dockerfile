# Dockerfile
#tel_ID = "your-telegram-api-id" # Dit telegram bot API ID
#rec_ID = "your-telegram-recipient-id" # Telegram modtager ID

# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

VOLUME /app/logs

# Set environment variables
ENV TELEGRAM_API=min_default_telegram_api
ENV TELEGRAM_REC=min_default_telegram_rec

#libtool autoconf automake
#libfftw3-dev screen
#fakeroot debhelper librtlsdr-dev 
#pkg-config libncurses5-dev libbladerf-dev
#libhackrf-dev liblimesuite-dev

#    libusb-1.0-0-dev \

RUN wget -O  /etc/udev/rules.d/rtl-sdr.rules "https://raw.githubusercontent.com/osmocom/rtl-sdr/master/rtl-sdr.rules"

# Install necessary packages
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    librtlsdr-dev \
    libfftw3-dev \
    libtool \
    autoconf \
    automake \
    screen \
    fakeroot \
    debhelper \
    pkg-config \
    libncurses5-dev \
    libbladerf-dev \
    libhackrf-dev \
    liblimesuite-dev \
    git \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Clone and build rtl-sdr
#     git checkout 0.6.0 && \
RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    cd rtl-sdr && \
    mkdir build && \
    cd build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && \
    make install && \
    ldconfig

# Install additional packages for multimon-ng
RUN apt-get update && apt-get install -y \
    qtbase5-dev \
    libpulse-dev \
    libx11-dev && \
    rm -rf /var/lib/apt/lists/* 

# Clone and build multimon-ng
RUN git clone https://github.com/EliasOenal/multimon-ng.git && \
    cd multimon-ng && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make && \
    make install

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY app.py /app/app.py
COPY config.txt /app/config.txt

# Command to run the application
CMD [ "python", "-u", "app.py" ]
