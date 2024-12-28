[![Docker Build and Push to DockerHub](https://github.com/joachimth/PythonPagerTelegramForwarder/actions/workflows/docker_build_push.yml/badge.svg?branch=main)](https://github.com/joachimth/PythonPagerTelegramForwarder/actions/workflows/docker_build_push.yml)

# PythonPagerTelegramForwarder

Denne Python-baserede applikation modtager data fra en RTL-SDR-radio, dekoder meddelelser ved hjælp af multimon-ng, og sender beskeder til en bestemt Telegram-bruger eller -gruppe ved hjælp af en Telegram-bot.

## Funktionalitet
1. Modtager radiosignaler fra en RTL-SDR-enhed.
2. Dekoder meddelelser ved hjælp af **multimon-ng** og **rtl_fm**.
3. Filtrerer relevante data baseret på konfigurationsindstillinger.
4. Sender beskeder til Telegram-brugere eller -grupper ved hjælp af en bot.
5. Flask-baseret interface til at administrere konfiguration og logfiler.

---

## Installation

### Forudsætninger
- En funktionel RTL-SDR-enhed.
- Docker installeret på værtsmaskinen.
- Telegram API-token (oprettes via [BotFather](https://core.telegram.org/bots#botfather)).

### Installation via Docker
1. Hent Docker-billedet:
   ```bash
   docker pull joachimth/pythonpagertelegramforwarder
   ```

2. Kør containeren med adgang til en bestemt USB-enhed:
   ```bash
   docker run -e TELEGRAM_API='din_telegram_api' -e TELEGRAM_REC='din_telegram_rec' \
              -d --name pythonpagertelegramforwarder --device=/dev/bus/usb/001/001 \
              joachimth/pythonpagertelegramforwarder:latest
   ```

   **Bemærk:** Sørg for, at stien `/dev/bus/usb/001/001` svarer til din RTL-SDR-enhed.

3. Alternativt kan du give adgang til alle USB-enheder:
   ```bash
   docker run -e TELEGRAM_API='din_telegram_api' -e TELEGRAM_REC='din_telegram_rec' \
              -d --name pythonpagertelegramforwarder --device=/dev/bus/usb \
              joachimth/pythonpagertelegramforwarder:latest
   ```

---

## Konfiguration
Applikationen bruger en `config.txt`-fil til at administrere indstillinger. Denne fil indeholder:
- Telegram API-token og modtager-ID (`TELEGRAM_API`, `TELEGRAM_REC`).
- Multimon-ng konfigurationer.
- Radiokonfigurationer.

### Eksempel på `config.txt`
```txt
frequency=144800000
ppm=0
modulation=AFSK
telegram_api=din_telegram_api
telegram_rec=din_telegram_rec
```

---

## Flask Interface
Applikationen leverer et Flask-baseret interface til:
- Ændring af `config.txt` efter opstart.
- Gennemgang af logfiler (`kalrun.log` og `multimon.log`).

For at tilgå interfacet:
1. Åbn din browser og naviger til `http://localhost:5000`.
2. Log ind med de nødvendige oplysninger.

---

## Programmets Workflow
1. **Kalibrering:** Applikationen starter med at kalibrere ppm-fejl baseret på GSM-signaler.
2. **Lytning:** RTL_FM begynder at lytte på den specificerede frekvens.
3. **Dekodning:** Multimon-ng dekoder signalerne baseret på indstillingerne.
4. **Telegram:** Relevante beskeder sendes til den specificerede Telegram-bruger/-gruppe.

---

## Fejlfinding
- **Problem med USB-adgang:** Tjek tilladelser for din USB-enhed med `lsusb` og opdater dine Docker-indstillinger.
- **Manglende Telegram-beskeder:** Bekræft, at API-token og modtager-ID er korrekte i `config.txt`.
- **Flask-interface ikke tilgængeligt:** Sørg for, at containeren kører, og at port 5000 ikke er i brug af andre applikationer.

---

## Ressourcer
- [RTL-SDR](https://www.rtl-sdr.com/)
- [Multimon-ng](https://github.com/EliasOenal/multimon-ng)
- [Telegram Bots API](https://core.telegram.org/bots)

---

## Licens
Dette projekt er udgivet under MIT-licensen. Se [LICENSE](LICENSE) for detaljer.

---

## Kontakt
- **Forfatter:** Joachim Thirsbro
- **GitHub:** [joachimth](https://github.com/joachimth)

---

## Bidrag
Pull requests er velkomne. For større ændringer, diskuter venligst først dine forslag via [Issues](https://github.com/joachimth/PythonPagerTelegramForwarder/issues).
