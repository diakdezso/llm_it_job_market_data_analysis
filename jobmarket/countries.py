"""All European countries (incl. Turkey, as Eurostat reports it) and the seed function."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from jobmarket.models import Country

# iso2, iso3, eurostat_code, name, eu_member, currency
EUROPEAN_COUNTRIES = [
    ("AL", "ALB", "AL", "Albania", False, "ALL"),
    ("AD", "AND", "AD", "Andorra", False, "EUR"),
    ("AT", "AUT", "AT", "Austria", True, "EUR"),
    ("BY", "BLR", "BY", "Belarus", False, "BYN"),
    ("BE", "BEL", "BE", "Belgium", True, "EUR"),
    ("BA", "BIH", "BA", "Bosnia and Herzegovina", False, "BAM"),
    ("BG", "BGR", "BG", "Bulgaria", True, "EUR"),
    ("HR", "HRV", "HR", "Croatia", True, "EUR"),
    ("CY", "CYP", "CY", "Cyprus", True, "EUR"),
    ("CZ", "CZE", "CZ", "Czechia", True, "CZK"),
    ("DK", "DNK", "DK", "Denmark", True, "DKK"),
    ("EE", "EST", "EE", "Estonia", True, "EUR"),
    ("FI", "FIN", "FI", "Finland", True, "EUR"),
    ("FR", "FRA", "FR", "France", True, "EUR"),
    ("DE", "DEU", "DE", "Germany", True, "EUR"),
    ("GR", "GRC", "EL", "Greece", True, "EUR"),
    ("HU", "HUN", "HU", "Hungary", True, "HUF"),
    ("IS", "ISL", "IS", "Iceland", False, "ISK"),
    ("IE", "IRL", "IE", "Ireland", True, "EUR"),
    ("IT", "ITA", "IT", "Italy", True, "EUR"),
    ("XK", "XKX", "XK", "Kosovo", False, "EUR"),
    ("LV", "LVA", "LV", "Latvia", True, "EUR"),
    ("LI", "LIE", "LI", "Liechtenstein", False, "CHF"),
    ("LT", "LTU", "LT", "Lithuania", True, "EUR"),
    ("LU", "LUX", "LU", "Luxembourg", True, "EUR"),
    ("MT", "MLT", "MT", "Malta", True, "EUR"),
    ("MD", "MDA", "MD", "Moldova", False, "MDL"),
    ("MC", "MCO", "MC", "Monaco", False, "EUR"),
    ("ME", "MNE", "ME", "Montenegro", False, "EUR"),
    ("NL", "NLD", "NL", "Netherlands", True, "EUR"),
    ("MK", "MKD", "MK", "North Macedonia", False, "MKD"),
    ("NO", "NOR", "NO", "Norway", False, "NOK"),
    ("PL", "POL", "PL", "Poland", True, "PLN"),
    ("PT", "PRT", "PT", "Portugal", True, "EUR"),
    ("RO", "ROU", "RO", "Romania", True, "RON"),
    ("RU", "RUS", "RU", "Russia", False, "RUB"),
    ("SM", "SMR", "SM", "San Marino", False, "EUR"),
    ("RS", "SRB", "RS", "Serbia", False, "RSD"),
    ("SK", "SVK", "SK", "Slovakia", True, "EUR"),
    ("SI", "SVN", "SI", "Slovenia", True, "EUR"),
    ("ES", "ESP", "ES", "Spain", True, "EUR"),
    ("SE", "SWE", "SE", "Sweden", True, "SEK"),
    ("CH", "CHE", "CH", "Switzerland", False, "CHF"),
    ("TR", "TUR", "TR", "Turkey", False, "TRY"),
    ("UA", "UKR", "UA", "Ukraine", False, "UAH"),
    ("GB", "GBR", "UK", "United Kingdom", False, "GBP"),
    ("VA", "VAT", "VA", "Vatican City", False, "EUR"),
]


def seed_countries(session: Session) -> None:
    """Insert the countries that are not in the table yet."""
    existing = set(session.scalars(select(Country.iso2)))
    session.add_all(
        Country(iso2=iso2, iso3=iso3, eurostat_code=es, name=name, eu_member=eu, currency=cur)
        for iso2, iso3, es, name, eu, cur in EUROPEAN_COUNTRIES if iso2 not in existing)
    session.commit()
