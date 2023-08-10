# === Build Stage 1: Setting up RTL-SDR and necessary tools ===
FROM python:3.8-slim-buster as builder

# Set working directory
WORKDIR /app

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

COPY rtl-sdr.rules /etc/udev/rules.d/rtl-sdr.rules
RUN echo "blacklist dvb_usb_rtl28xxu" >> /etc/modprobe.d/blacklist.conf
RUN echo "blacklist dvb_usb_rtl8xxxu" >> /etc/modprobe.d/blacklist.conf
RUN echo "blacklist 8192cu" >> /etc/modprobe.d/blacklist.conf

# === Build Stage 2: Final Stage with application code and Python dependencies ===
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

# Install necessary packages
RUN apt-get update && apt-get install -y \
    librtlsdr-dev \
    libfftw3-dev \
    libtool \
    libncurses5-dev \
    libhackrf-dev \
    qtbase5-dev \
    libpulse-dev \
    libx11-dev \
    usbutils \
    wget \
    htop \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV TELEGRAM_API=min_default_telegram_api
ENV TELEGRAM_REC=min_default_telegram_rec

VOLUME /app/logs

EXPOSE 5000

ARG DOCKER_IMAGE_VERSION

# Copy built binaries from builder stage
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
COPY --from=builder /usr/local/include/ /usr/local/include/


# Copy requirements.txt and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt && \
    set-cont-env APP_NAME "PythonPagerTelegramForwarder" && \
    set-cont-env DOCKER_IMAGE_VERSION "$DOCKER_IMAGE_VERSION"

# Copy application code
COPY app.py /app/app.py
COPY config.txt /app/config.txt
COPY flaskapp.py /app/flaskapp.py
COPY kal_automation.py /app/kal_automation.py
COPY templates/admin.html /app/templates/admin.html
COPY templates/login.html /app/templates/login.html
COPY templates/log.html /app/templates/log.html
COPY init.py /app/init.py

# Command to run the application
CMD [ "python", "init.py" ]
#CMD [ "sleep", "infinity" ]

# Metadata.
LABEL \
      org.label-schema.name="pptf" \
      org.label-schema.description="Docker container for PythonPagerTelegramForwarder" \
      org.label-schema.version="${DOCKER_IMAGE_VERSION:-}" \
      org.label-schema.vcs-url="https://github.com/joachimth/PythonPagerTelegramForwarder" \
      org.label-schema.schema-version="1.0"
