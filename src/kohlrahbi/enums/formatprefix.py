from enum import Enum


class FormatPrefix(Enum):
    # UTILities Master Data message
    # Stammdaten zu Kundendaten, Verträgen und Zählpunkten
    UTILMD = 11

    # Metered Services CONSumption report message
    # Verbrauchszählerwerte
    MSCONS = 13

    # Offer production
    # Angebotserstellung
    QUOTES = 15

    # Purchase ORDERS message
    # Bestellung
    ORDERS = 17

    # Purchase ORDer ReSPonse message
    # Antwort auf eine Bestellung
    ORDRSP = 19

    # STAtus of transport
    # Statusnachricht einer Lieferung
    IFTSTA = 21

    # INSpection RePorT
    # Prüfbericht
    INSRPT = 23

    # UTILities Time Series message
    UTILTS = 25

    # PRIce CATalogue message
    # Preisliste / Katalog
    PRICAT = 27

    # COMmercial DISpute
    COMDIS = 29

    # INVOICe message
    # Rechnung
    INVOIC = 31

    # REMittance ADVice
    # Zahlungsavise
    REMADV = 33

    # REQuest of quOTE
    # Angebotsanfrage
    REQOTE = 35

    # PARTy INformation message
    PARTIN = 37

    # purchase ORDer CHanGe message
    # Änderungsmittelung einer Bestellung
    ORDCHG = 39

    SSQNOT = 70
