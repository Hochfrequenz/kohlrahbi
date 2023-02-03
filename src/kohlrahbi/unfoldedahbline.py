from attrs import define


@define(auto_attribs=True, kw_only=True)
class UnfoldedAhbLine:
    index: int
    segment_name: str  # Ansprechpartner
    segment_gruppe: str | None  # SG3
    segment: str | None  # CTA
    datenelement: str | None  # 3055
    code: str | None  # IC
    qualifier: str | None  # Name vom Ansprechpartner
    beschreibung: str | None  # Informationskontakt
    bedinung_ausdruck: str | None  # Muss / X / X [1P0..1]
    bedingung: str | None  # [492] Wenn MP-ID in NAD+MR (Nachrichtenempfänger) aus Sparte Strom
