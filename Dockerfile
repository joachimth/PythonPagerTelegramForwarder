# === Build Stage 1: Setting up RTL-SDR and necessary tools ===
FROM python:3.10-slim-buster as builder

LABEL maintainer="Joachim Thirsbro <joachim@thirsbro.dk>"

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    librtlsdr-dev \
    libfftw3-dev \
    libtool \
    autoconf \
    automake \
    fakeroot \
    debhelper \
    pkg-config \
    libncurses5-dev \
    libbladerf-dev \
    libhackrf-dev \
    liblimesuite-dev \
    git \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Clone and build rtl-sdr
RUN git clone https://github.com/joachimth/rtl-sdr.git && \
    cd rtl-sdr && mkdir build && cd build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON && \
    make && make install && ldconfig

# Clone and build multimon-ng
RUN git clone https://github.com/joachimth/multimon-ng.git && \
    cd multimon-ng && mkdir build && cd build && \
    cmake .. && make && make install

# Clone and build kalibrate-rtl
RUN git clone https://github.com/joachimth/kalibrate-rtl.git && \
    cd kalibrate-rtl && ./bootstrap && ./configure && \
    make && make install

# Set up udev rules for RTL-SDR
COPY rtl-sdr.rules /etc/udev/rules.d/rtl-sdr.rules
RUN echo "blacklist dvb_usb_rtl28xxu" >> /etc/modprobe.d/blacklist.conf && \
    echo "blacklist dvb_usb_rtl8xxxu" >> /etc/modprobe.d/blacklist.conf && \
    echo "blacklist 8192cu" >> /etc/modprobe.d/blacklist.conf

# === Build Stage 2: Final Stage with application code and Python dependencies ===
FROM python:3.10-slim-buster

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    librtlsdr-dev \
    libfftw3-dev \
    libncurses5-dev \
    libhackrf-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TELEGRAM_API=min_default_telegram_api \
    TELEGRAM_REC=min_default_telegram_rec

# Define volume for logs
VOLUME /app/logs

# Expose port for Flask
EXPOSE 5000

# Copy built binaries from builder stage
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define default command
CMD ["python", "init.py"]

# Metadata
LABEL \
    org.label-schema.name="pptf" \
    org.label-schema.description="Docker container for PythonPagerTelegramForwarder" \
    org.label-schema.version="${DOCKER_IMAGE_VERSION:-}" \
    org.label-schema.vcs-url="https://github.com/joachimth/PythonPagerTelegramForwarder" \
    org.label-schema.schema-version="1.0"
