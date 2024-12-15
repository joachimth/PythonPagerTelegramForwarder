# PythonPagerTelegramForwarder

## IKKE FÆRDIG README.MD

## Generel Beskrivelse
>PythonPagerTelegramForwarder er en applikation designet til at modtage og dekode data fra en radioreceiver ved hjælp af multimon-ng og rtl_fm. Hvis dataene opfylder specifikke kriterier, sender applikationen en besked via Telegram bot. Den bruger også en konfigurationsfil til at indlæse specifikke indstillinger.

## Installation
>Hent DockerHub Image.
```bash
docker pull joachimth/pythonpagertelegramforwarder
```

## Vigtigt, adgang til USB enhed eller enheder. Der er to løsninger.
> Bemærk, at adgang til USB-enheder fra en Docker-container kan være begrænset af sikkerhedspolitikker på din værtsmaskine. Hvis du støder på problemer, skal du sørge for, at du har de nødvendige tilladelser til at få adgang til USB-enheder fra din Docker-container.

### Løsning 1. Adgang til en usb enhed, her RTL-SDR Dongle.

>For at give din Docker-container adgang til USB-enheden (RTL-SDR), skal du bruge `--device` flag ved kør kommandoen. Her er hvordan du kan gøre det:

```bash
docker run  -e TELEGRAM_API='din_telegram_api' -e TELEGRAM_REC='din_telegram_rec'  -d --name=joachimth/pythonpagertelegramforwarder --device=/dev/bus/usb/001/001 joachimth/pythonpagertelegramforwarder:latest
```

I ovenstående kommando, er `/dev/bus/usb/001/001` stien til din USB-enhed. Du skal udskifte det med stien til din RTL-SDR-enhed. Du kan finde denne sti ved at køre `lsusb` kommando på din værtsmaskine.

### Løsning 2. Adgang til alle usb enheder.

> Alternativt, kan der gives adgang til alle usb enheder til Docker containeren, kan du også bruge `--device=/dev/bus/usb` flag, som giver Docker containeren adgang til alle USB-enheder:

```bash
docker run -e TELEGRAM_API='din_telegram_api' -e TELEGRAM_REC='din_telegram_rec' -d --name=joachimth/pythonpagertelegramforwarder --device=/dev/bus/usb joachimth/pythonpagertelegramforwarder:latest
```

## Konfiguration
> Der er inkluderet en config.txt . Denne indeholder de vigtigste elementer som kan ændres.

### Telegram API
> For at opnå adgang til at modtage beskederne, skal du have oprettet adgang til Telegram via Botfather. Disse værdier skal inkluderes som ENV, miljøvariabler ved opstart af Docker containeren. Det drejer sig om følgende værdier:

```bash

-e TELEGRAM_API='din_telegram_api'

-e TELEGRAM_REC='din_telegram_rec'

```

TODO Sådan finder du disse værdier.

## Flask interface, til simple ændringer i config.txt efterfølgende, samt til kontrol af kalrun.log og multimon.log.
> Beskrivelse mangler her.

## Programmets funktion.
### Step 1. Kalibrering af fejl ppm ved hjælp af GSM nettet. Dette tager ved opstart 5-10 minutter.
### Step 2. Rtlfm starter op, og lytter til den angivne frekvens, og leverer indholdet direkte videre til multimon-ng.
### Step 3. Multimon-ng dekoder signalet ud fra de konfigurationer som er angivet i config.txt


## Made by Joachim Thirsbro.
