# Dockerfile
#tel_ID = "your-telegram-api-id" # Dit telegram bot API ID
#rec_ID = "your-telegram-recipient-id" # Telegram modtager ID

# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

VOLUME /app/logs

# Fortæl Docker at appen lytter på port 5000
EXPOSE 5000

# Set environment variables
ENV TELEGRAM_API=min_default_telegram_api
ENV TELEGRAM_REC=min_default_telegram_rec

#libtool autoconf automake
#libfftw3-dev screen
#fakeroot debhelper librtlsdr-dev 
#pkg-config libncurses5-dev libbladerf-dev
#libhackrf-dev liblimesuite-dev

#    libusb-1.0-0-dev \
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
    wget \
    curl \
    htop \
    coreutils \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Clone and build rtl-sdr
RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    cd rtl-sdr && \
    mkdir build && \
    cd build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && \
    make install && \
    ldconfig

RUN wget -O /etc/udev/rules.d/rtl-sdr.rules "https://raw.githubusercontent.com/osmocom/rtl-sdr/master/rtl-sdr.rules"
RUN echo "blacklist dvb_usb_rtl28xxu" >> /etc/modprobe.d/blacklist.conf
RUN echo "blacklist dvb_usb_rtl8xxxu" >> /etc/modprobe.d/blacklist.conf
RUN echo "blacklist 8192cu" >> /etc/modprobe.d/blacklist.conf

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

# Clone and build kalibrate-rtl
RUN git clone https://github.com/steve-m/kalibrate-rtl.git && \
    cd kalibrate-rtl && \
    ./bootstrap && \
    ./configure && \
    make && \
    make install

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY app.py /app/app.py
COPY config.txt /app/config.txt
COPY flaskapp.py /app/flaskapp.py
COPY kal_automation.py /app/kal_automation.py
COPY admin.html /app/admin.html
COPY login.html /app/login.html
COPY log.html /app/log.html
COPY init.py /app/init.py

# Command to run the application
CMD [ "python", "-u", "init.py" ]
#CMD [ "sleep", "infinity" ]
