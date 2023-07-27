# Python Pager Telegram Forwarder

Denne Python-baserede applikation modtager data fra en RTL-SDR radio, dekoder meddelelser ved hjælp af `multimon-ng`, og sender beskeder til en bestemt Telegram-bruger eller -gruppe ved hjælp af en Telegram bot.

## Installation

Du skal bruge Python3 samt nogle eksterne pakker, der kan installeres med pip:

```bash
pip install pytgbot configparser
```

Du skal også sørge for at have både `rtl_fm` og `multimon-ng` installeret på din maskine. Du kan finde installationsinstruktioner til disse på deres respektive hjemmesider.

## Brug

Applikationen læser konfigurationsdata fra en fil ved navn `config.txt`, der skal være placeret i samme mappe som scriptet. `config.txt` skal indeholde følgende sektioner og indstillinger:

```txt
[Frequencies]
freq = "171.300M" # Frekvensen som skal modtages
prot = "POCSAG2400 POCSAG1200" # Protokoller som skal afkodes. Flere protokoller kan tilføjes adskilt med mellemrum
min_len = "10" # Minimum længde for beskeder, der skal videresendes
tel_ID = "your-telegram-api-id" # Dit telegram bot API ID
rec_ID = "your-telegram-recipient-id" # Telegram modtager ID

[rtl_fm]
device_index = "0" # Enhedsindex for rtl_fm
sample_rate = "22050" # Sample rate for rtl_fm
enable_option = "-E dc" # Aktiver yderligere optioner for rtl_fm
gain = "42" # Gain for rtl_fm
ppm_error = "33" # PPM-fejl for rtl_fm
squelch_level = "0" # Squelch-niveau for rtl_fm

[multimon-ng]
input_file = "/dev/stdin" # Input fil for multimon-ng

[Encoding]
encoding_format = "iso-8859-1" # Tekst dekodningsformat. F.eks. "iso-8859-1", "utf-8" osv.
```

Efter du har konfigureret `config.txt` med dine specifikke indstillinger, kan du køre scriptet ved at udføre følgende kommando i terminalen:

```bash
python3 pager_telegram_forwarder.py
```

Husk at erstatte `"your-telegram-api-id"` og `"your-telegram-recipient-id"` med dine rigtige Telegram API og modtager ID'er.

## Fejlfinding

Hvis du støder på fejl, kan du tjekke logfilen `error.log` i samme mappe som scriptet. Denne logfil indeholder detaljerede oplysninger om eventuelle fejl, der måtte opstå under kørsel af scriptet.
