# AHB Extractor
![Unittests status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/AHBExtractor/workflows/Black/badge.svg)


This tool helps to generate machine readable files from AHB documents.
## Installation
The AHB Extractor is a Python based tool. Therefor you have to make sure, that Python is running on your machine.
### Without tox

Create a new virtual environment
```bash
python -m venv .venv
```
Activate it
#### Windows
```
.venv\Scripts\activate
```
#### MacOS/Linux
```
source .venv/bin/activate
```

Install the requirements with
```
pip install -r requirements.txt
```
Done.
### With tox
If tox is installed system-wide, then you can just run
```
tox -e dev
```
in the root directory.

## Execution

At the moment you have to define the filename of the AHB you want to extract in [`ahbextractor\ahbextractor.py`](./ahbextractor/ahbextractor.py).

If the filename is set, you can run the script with
```bash
python -m ahbextractor
```
You should see some output like this in your terminal
```
🔍 Extracting Pruefidentifikatoren: 11039, 11040, 11041
💥 The Excel file 11039.xlsx is open. Please close this file and try again.
💾 Saved file for Pruefidentifikator 11040
💾 Saved file for Pruefidentifikator 11041
```

## PDF Documents

The following sections give a short overview where to find the start and end for the Formate.

## APERAK (Fehlermeldung)
* Datei: `CONTRL_APERAK_AHB_2_3h_20201016.pdf`
* Start: `4.2 Tabellarische Darstellung der APERAK`
* Ende einschließlich: `4.2 Tabellarische Darstellung der APERAK`

## IFTSTA (Infomeldung)
* Dateiname: `IFTSTA_AHB_2_0b_20201016.pdf`
* Start: `4.1 Übermittlung des Status des Gesamtvorgangs im Rahmen des MSB-Wechsels 1/2`
* Ende einschließlich: `4.9 Information zur Ablehnung eines Angebots oder einer Anfrage`

## INSRPT (Prüfbericht)
* Datei: `INSRPT_AHB_1_1f_Lesefassung_20191002.pdf`
* Start: `3.1 Anwendungsfälle: Störungsmeldung, Ablehnung bzw. Bestätigung der Störungsmeldung und Ergebnisbericht`
* Ende einschließlich: `3.3 Anwendungsfälle: Informationsmeldungen des MSB in der Sparte Strom`

## INVOIC (Rechnung)
* Datei: `INVOIC_REMADV_AHB_2_4_Lesefassung_20200701.pdf`
* Start: `2.1.1 Abschlags-, NN-, WiM- und MSB-Rechnung`
* Ende einschließlich: `2.1.4 Kapazitätsrechnung`
* Start: `3.1 Anwendungsfälle REMADV`
* Ende einschließlich: `3.1 Anwendungsfälle REMADV`
## MSCONS (Messwerte und Zählerstände)
* Datei: `MSCONS_AHB_2_3c_20201001_v2.pdf`
* Start: `4.2 Anwendungsübersicht Messwert Lastgang`
* Ende einschließlich: `4.2 Anwendungsübersicht Messwert Lastgang`
* Start: `4.4 Anwendungsübersicht Messwert Energiemenge`
* Ende einschließlich: `4.4 Anwendungsübersicht Messwert Energiemenge`
* Start: `4.6 Anwendungsübersicht Messwert Zählerstand`
* Ende einschließlich: `4.6 Anwendungsübersicht Messwert Zählerstand`
* Start: `4.8 Anwendungsübersicht Messwert Storno`
* Ende einschließlich: `4.8 Anwendungsübersicht Messwert Storno`
* Start: `4.10Anwendungsübersicht Bilanzkreissummen`
* Ende einschließlich: `4.10Anwendungsübersicht Bilanzkreissummen`
* Start: `4.12Anwendungsübersicht Normiertes Profil / Profilschar / Vergangenheitsw. TEP`
* Ende eischließlich: `4.12Anwendungsübersicht Normiertes Profil / Profilschar / Vergangenheitsw. TEP`
* Start: `4.14Anwendungsübersicht EEG-Überführungszeitreihen`
* Ende einschließlich: `4.14Anwendungsübersicht EEG-Überführungszeitreihen`
* Start: `4.16Anwendungsübersicht Gasbeschaffenheitsdaten`
* Ende einschließlich: `4.16Anwendungsübersicht Gasbeschaffenheitsdaten`
* Start: `4.18Anwendungsübersicht Allokationsliste Gas / bilanzierte Menge Strom/Gas`
* Ende einschließlich: `4.18Anwendungsübersicht Allokationsliste Gas / bilanzierte Menge Strom/Gas`
* Start: `4.20Anwendungsübersicht Bewegungsdaten im Kalenderjahr vor Lieferbeginn`
* Ende einschließlich: `4.20Anwendungsübersicht Bewegungsdaten im Kalenderjahr vor Lieferbeginn`
* Start: `4.22Anwendungsübersicht Energiemenge und Leistungsmaximum`
* Ende einschließlich: `4.22Anwendungsübersicht Energiemenge und Leistungsmaximum`

## ORDERS (Bestellung)
* Datei: `REQOTE_QUOTES_ORDERS_ORDRSP_AHB_1_0c_20201001.pdf`
* Start: `3.1.1 Anfrage zur Übermittlung von Stammdaten im Initialprozess`
* Ende einschließlich: `3.5 Reklamation von Werten/Lastgängen`
* Start: `3.6.1 Anforderung eines Geräteübernahmeangebots (REQOTE)`
* Ende einschließlich: `3.10.4 Bestätigung bzw. Ablehnung der Beendigung der Rechnungsabwicklung des Messstellenbetriebs über den LF (ORDRSP`

## ORDRSP (Bestellantwort)
* Datei: `REQOTE_QUOTES_ORDERS_ORDRSP_AHB_1_0c_20201001.pdf`
* selbe Datei wie `ORDERS (Bestellung)`

## QUOTES (Angebot)
* Datei: `REQOTE_QUOTES_ORDERS_ORDRSP_AHB_1_0c_20201001.pdf`
* selbe Datei wie `ORDERS (Bestellung)`

## REQOTE (Anfrage)
* Datei: `REQOTE_QUOTES_ORDERS_ORDRSP_AHB_1_0c_20201001.pdf`
* selbe Datei wie `ORDERS (Bestellung)`

## UTILMD (Stammdaten)
* Datei: `UTILMD_AHB_Stammdatenänderung_1_1b_20201016.pdf`
* Start: `8.1 Nicht bilanzierungsrelevante Änderung vom LF ohne Abhängigkeiten (jedes Stammdatum kann einzeln übermittelt werden)`
* Ende einschließlich: `9.10 Anfrage zur Stammdatenänderung von ÜNB`

## UTILTS (Berechnungsformel)
* Datei: `UTILTS_AHB_Berechnungsformel_1_0b_20201016.pdf`
* Start: `4 Übermittlung der Berechnungsformel`
* Ende einschließlich: `4 Übermittlung der Berechnungsformel`
