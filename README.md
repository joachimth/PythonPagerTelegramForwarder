# Python Pager Telegram Forwarder
#Test2
Denne Python-baserede applikation modtager data fra en RTL-SDR radio, dekoder meddelelser ved hjælp af `multimon-ng`, og sender beskeder til en bestemt Telegram-bruger eller -gruppe ved hjælp af en Telegram bot.

## Fil- og Mappestruktur

Projektets struktur ser således ud:

pagerbot/
│
├── Dockerfile
├── README.md
├── requirements.txt
├── app.py
└── config.txt

Hver fil har følgende formål:

- `Dockerfile`: Indeholder instruktionerne til at bygge Docker containeren. Denne fil klargører miljøet, hvori applikationen skal køre, og inkluderer installation af de nødvendige afhængigheder.
  
- `README.md`: Indeholder dokumentation for projektet, herunder hvordan man bygger og kører Docker containeren.
  
- `requirements.txt`: Lister de Python-pakker, der er nødvendige for at køre Python-scriptet. Disse pakker installeres i Docker containeren.
  
- `app.py`: Dette er Python-scriptet, der udfører det egentlige arbejde. Scriptet lytter til RF-signaler, dekoder POCSAG-beskederne, og sender dem til en Telegram-modtager.
  
- `config.txt`: Denne fil indeholder konfigurationsdata, som Python-scriptet anvender. Konfigurationsdataene inkluderer detaljer som frekvens, protokoller, minimum beskedlængde, Telegram API ID, og Telegram modtager ID.

## Bygge Docker Containeren

For at bygge Docker containeren, naviger til projektets rodmappe (hvor Dockerfile ligger), og kør følgende kommando:

```bash
docker build -t pagerbot-container .

Køre Docker Containeren

Efter at have bygget Docker containeren, kan du køre den med følgende kommando:

docker run --privileged -v /dev/bus/usb:/dev/bus/usb pagerbot-container

Bemærk at --privileged flaget og -v /dev/bus/usb:/dev/bus/usb optionen sikrer, at Docker containeren har adgang til USB-enheder på host-maskinen.

Sikkerhedsadvarsel

Kørsel af en Docker container med --privileged tillader containeren at få adgang til alle enheder på host-maskinen, hvilket kan have sikkerhedsmæssige implikationer. Brug denne indstilling med forsigtighed, og kun hvis det er nødvendigt for dit anvendelsesområde.

Og husk at opdatere `Dockerfile` med det nye navn til Docker containeren:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run pager_telegram_forwarder.py when the container launches
CMD ["python", "app.py"]

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

Husk at erstatte `"your-telegram-api-id"` og `"your-telegram-recipient-id"` med dine rigtige Telegram API og modtager ID'er.

## Fejlfinding

Hvis du støder på fejl, kan du tjekke logfilen `error.log` i samme mappe som scriptet. Denne logfil indeholder detaljerede oplysninger om eventuelle fejl, der måtte opstå under kørsel af scriptet.
