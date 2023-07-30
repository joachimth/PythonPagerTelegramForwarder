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
