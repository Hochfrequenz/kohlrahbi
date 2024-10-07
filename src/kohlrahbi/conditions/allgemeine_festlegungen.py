# pylint: disable=line-too-long
"""
Contains conditions for times in allgemeine Festlegungen.
"""
# We decided against adding the time_packages to the regular packages.
# The time-packages are resolved by a special transformer in AHBicht:
# https://github.com/Hochfrequenz/ahbicht/blob/c51c81d2be098dd79ff52b754979892396207fe2/src/ahbicht/expressions/expression_resolver.py#L149

time_conditions = {
    "490": "wenn Wert in diesem DE, an der Stelle CCYYMMDDHHMM ein Zeitpunkt aus dem angegeben Zeitraum der Tabelle Kapitel 3.5 „Übersicht gesetzliche deutsche Sommerzeit (MESZ)“ der Spalten:\n›\t„Sommerzeit (MESZ) von“ Darstellung in UTC und\n›\t„Sommerzeit (MESZ) bis“ Darstellung in UTC ist.",
    "491": "wenn Wert in diesem DE, an der Stelle CCYYMMDDHHMM ein Zeitpunkt aus dem angegeben Zeitraum der Tabelle Kapitel 3.6 „Übersicht gesetzliche deutsche Zeit (MEZ)“ der Spalten: \n›\t„Winterzeit (MEZ) von“ Darstellung in UTC und\n›\t„Winterzeit (MEZ) bis“ Darstellung in UTC ist.",
    "492": "wenn MP-ID in NAD+MR aus Sparte Strom",
    "493": "wenn MP-ID in NAD+MR aus Sparte Gas",
    "931": "Format: ZZZ = +00",
    "932": "Format: HHMM = 2200",
    "933": "Format: HHMM = 2300",
    "934": "Format: HHMM = 0400",
    "935": "Format: HHMM = 0500",
}
