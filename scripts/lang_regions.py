#!/usr/bin/env python3
"""Region -> language tables for the entry-time language detector.

THE LIMITATION, STATED UP FRONT
-------------------------------
This site is static GitHub Pages. There is no server, so there is no request
IP to look at, and no Accept-Language header we can read. The only honest
client-side proxies for "where is this visitor" are:

  1. `Intl.DateTimeFormat().resolvedOptions().timeZone` — the IANA zone the
     device's clock is set to (e.g. "Asia/Tokyo", "Europe/Berlin").
  2. the region subtag of the device locale ("en-DE" -> DE).

Neither is a location. A traveller carries their home timezone in their laptop
for a week; a Japanese expat in Berlin has Europe/Berlin; a VPN changes the IP
but not the clock. This is a *guess*, and it is deliberately ranked BELOW the
device language, which is the far stronger signal.

The rejected alternative was a geo-IP API call. That would send every single
visitor's IP address to a third party, and put a cross-origin round trip in
front of first paint on a site whose whole point is that it is static files.
Not worth it for a language default that one click overrides forever.

HOW THE TABLE IS SHAPED
-----------------------
Keyed on the LAST path segment of the zone ("Europe/Paris" -> "Paris",
"America/Argentina/Cordoba" -> "Cordoba"), because zone names are long and this
map ships inline in the <head> of all 143 pages. `assert_unique_cities()` is a
build-time check that no two zones in the table collapse onto the same city.

AREA_DEFAULT covers everything not named. Asia deliberately has NO default:
English is the working second language across Europe, the Americas, Oceania and
much of Africa, but it is not a safe blanket guess across Asia, so the Asian
regions where it genuinely is the lingua franca are named one by one and the
rest fall through to "no opinion" (which means: leave the visitor on whatever
page they landed on).
"""
from __future__ import annotations

# Zones -> language. Every judgement call that someone might reasonably
# disagree with carries its reason inline.
TZ_LANG = {
    "ja": [
        "Asia/Tokyo",
    ],
    "ko": [
        "Asia/Seoul", "Asia/Pyongyang",
    ],
    "zh": [
        "Asia/Shanghai", "Asia/Chongqing", "Asia/Chungking", "Asia/Harbin",
        "Asia/Urumqi", "Asia/Kashgar",
        # Taiwan, Hong Kong and Macau read Traditional Chinese; this site only
        # has Simplified. Same call as the zh-TW locale match: Simplified is a
        # far smaller gap for a Chinese reader than switching them to English.
        "Asia/Taipei", "Asia/Hong_Kong", "Asia/Macau",
    ],
    "id": [
        "Asia/Jakarta", "Asia/Pontianak", "Asia/Makassar", "Asia/Jayapura",
        # Malaysia and Brunei: Bahasa Melayu and Bahasa Indonesia are close
        # enough in writing that Indonesian reads far more naturally to a
        # Malaysian than English does. Judgement call.
        "Asia/Kuala_Lumpur", "Asia/Kuching", "Asia/Brunei",
    ],
    "tr": [
        "Europe/Istanbul",
        # Azerbaijani is Turkic and largely mutually intelligible with Turkish
        # in writing; Russian was the alternative and is a worse fit for
        # anyone under ~40 there.
        "Asia/Baku",
    ],
    "de": [
        "Europe/Berlin", "Europe/Vienna", "Europe/Zurich", "Europe/Busingen",
        "Europe/Vaduz",
    ],
    "it": [
        "Europe/Rome", "Europe/Vatican", "Europe/San_Marino",
    ],
    "fr": [
        "Europe/Paris", "Europe/Monaco",
        # Belgium is majority Dutch-speaking, but Dutch is not one of the 13
        # and French is; Luxembourg's administrative language is French.
        "Europe/Brussels", "Europe/Luxembourg",
        "Africa/Dakar", "Africa/Abidjan", "Africa/Kinshasa", "Africa/Lubumbashi",
        "Africa/Bamako", "Africa/Ouagadougou", "Africa/Niamey", "Africa/Conakry",
        "Africa/Libreville", "Africa/Brazzaville", "Africa/Douala",
        "Africa/Bangui", "Africa/Ndjamena", "Africa/Porto-Novo", "Africa/Lome",
        "Africa/Djibouti", "Indian/Antananarivo", "Indian/Reunion",
        "Indian/Mayotte", "America/Martinique", "America/Guadeloupe",
        "America/Cayenne", "America/Port-au-Prince",
    ],
    "es": [
        "Europe/Madrid", "Atlantic/Canary", "Africa/Ceuta",
        "Europe/Andorra",  # Catalan/Spanish; Spanish is the available one
        "America/Mexico_City", "America/Cancun", "America/Merida",
        "America/Monterrey", "America/Chihuahua", "America/Hermosillo",
        "America/Mazatlan", "America/Tijuana", "America/Ojinaga",
        "America/Argentina/Buenos_Aires", "America/Argentina/Cordoba",
        "America/Argentina/Mendoza", "America/Argentina/Salta",
        "America/Argentina/Tucuman", "America/Argentina/Jujuy",
        "America/Bogota", "America/Lima", "America/Santiago",
        "America/Punta_Arenas", "America/Caracas", "America/Guatemala",
        "America/Montevideo", "America/Asuncion", "America/La_Paz",
        "America/Havana", "America/Santo_Domingo", "America/Costa_Rica",
        "America/Panama", "America/Managua", "America/Tegucigalpa",
        "America/El_Salvador", "America/Guayaquil", "Pacific/Galapagos",
        "America/Puerto_Rico", "Africa/Malabo",
    ],
    "pt-br": [
        "America/Sao_Paulo", "America/Bahia", "America/Fortaleza",
        "America/Recife", "America/Manaus", "America/Belem", "America/Cuiaba",
        "America/Campo_Grande", "America/Porto_Velho", "America/Rio_Branco",
        "America/Noronha", "America/Maceio", "America/Araguaina",
        "America/Santarem", "America/Eirunepe", "America/Boa_Vista",
        # Portugal and Lusophone Africa: only Brazilian Portuguese exists here.
        # Same decision as the pt-PT locale match.
        "Europe/Lisbon", "Atlantic/Azores", "Atlantic/Madeira",
        "Atlantic/Cape_Verde", "Africa/Luanda", "Africa/Maputo",
        "Africa/Bissau", "Africa/Sao_Tome",
    ],
    "ar": [
        "Asia/Riyadh", "Asia/Dubai", "Asia/Qatar", "Asia/Kuwait",
        "Asia/Bahrain", "Asia/Muscat", "Asia/Baghdad", "Asia/Amman",
        "Asia/Beirut", "Asia/Damascus", "Asia/Gaza", "Asia/Hebron",
        "Asia/Aden", "Africa/Cairo", "Africa/Khartoum", "Africa/Tripoli",
        "Africa/Tunis", "Africa/Algiers", "Africa/Casablanca",
        "Africa/El_Aaiun", "Africa/Nouakchott", "Africa/Mogadishu",
        "Indian/Comoro",
    ],
    "ru": [
        "Europe/Moscow", "Europe/Kaliningrad", "Europe/Samara",
        "Europe/Volgograd", "Europe/Saratov", "Europe/Astrakhan",
        "Europe/Ulyanovsk", "Europe/Kirov", "Asia/Yekaterinburg", "Asia/Omsk",
        "Asia/Novosibirsk", "Asia/Krasnoyarsk", "Asia/Irkutsk", "Asia/Yakutsk",
        "Asia/Vladivostok", "Asia/Magadan", "Asia/Kamchatka", "Asia/Sakhalin",
        "Asia/Chita", "Asia/Novokuznetsk", "Asia/Barnaul", "Asia/Tomsk",
        "Asia/Anadyr", "Asia/Khandyga", "Asia/Ust-Nera", "Asia/Srednekolymsk",
        "Europe/Minsk", "Asia/Almaty", "Asia/Aqtobe", "Asia/Aqtau",
        "Asia/Atyrau", "Asia/Oral", "Asia/Qostanay", "Asia/Qyzylorda",
        "Asia/Bishkek", "Asia/Tashkent", "Asia/Samarkand", "Asia/Dushanbe",
        "Asia/Ashgabat", "Asia/Yerevan", "Asia/Tbilisi",
    ],
    "en": [
        # Asia only — every other AREA already defaults to en, so listing e.g.
        # Europe/London or America/New_York here would be dead weight in the
        # <head> of 143 pages. These are the Asian regions where English is
        # genuinely the working second language.
        "Asia/Kolkata", "Asia/Calcutta", "Asia/Colombo", "Asia/Dhaka",
        "Asia/Karachi", "Asia/Kathmandu", "Asia/Thimphu", "Asia/Singapore",
        "Asia/Manila", "Asia/Jerusalem", "Asia/Bangkok", "Asia/Ho_Chi_Minh",
        "Asia/Phnom_Penh", "Asia/Vientiane", "Asia/Yangon", "Asia/Nicosia",
        "Asia/Famagusta", "Asia/Kabul", "Asia/Tehran",
        # Deliberately NOT here: Asia/Ulaanbaatar, Asia/Seoul-adjacent gaps,
        # and every Central/East Asian zone not already claimed above. Those
        # fall through to "no opinion" -- see AREA_DEFAULT.
    ],
}

# Everything not named above. Asia has no entry on purpose (see module docs):
# an unmapped Asian zone yields NO OPINION, and the visitor is left where they
# landed -- which on the site root is Japanese, the documented final fallback.
AREA_DEFAULT = {
    "Europe": "en",
    "America": "en",
    "Africa": "en",
    "Australia": "en",
    "Pacific": "en",
    "Atlantic": "en",
    "Indian": "en",
}

# Region subtag of the device locale ("en-DE" -> DE), used only when the
# timezone is missing or unmapped -- a real case on browsers without Intl, and
# on locked-down clients that report Etc/UTC. Small on purpose: this signal is
# weaker than the timezone and much weaker than the language subtag that sits
# in front of it.
REGION_LANG = {
    "ja": ["JP"],
    "ko": ["KR", "KP"],
    "zh": ["CN", "TW", "HK", "MO", "SG"],
    "id": ["ID", "MY", "BN"],
    "tr": ["TR", "AZ", "CY"],
    "de": ["DE", "AT", "CH", "LI"],
    "it": ["IT", "SM", "VA"],
    "fr": ["FR", "BE", "LU", "MC", "SN", "CI", "CD", "CM", "ML", "BF", "NE",
           "GN", "GA", "CG", "TD", "BJ", "TG", "MG", "RE", "HT", "DJ"],
    "es": ["ES", "MX", "AR", "CO", "PE", "CL", "VE", "GT", "UY", "PY", "BO",
           "CU", "DO", "CR", "PA", "NI", "HN", "SV", "EC", "PR", "GQ", "AD"],
    "pt-br": ["BR", "PT", "AO", "MZ", "CV", "GW", "ST", "TL"],
    "ar": ["SA", "AE", "QA", "KW", "BH", "OM", "IQ", "JO", "LB", "SY", "PS",
           "YE", "EG", "SD", "LY", "TN", "DZ", "MA", "MR", "SO", "KM", "EH"],
    "ru": ["RU", "BY", "KZ", "KG", "UZ", "TJ", "TM", "AM", "GE"],
    "en": ["GB", "US", "CA", "AU", "NZ", "IE", "ZA", "IN", "PK", "BD", "LK",
           "NP", "PH", "SG", "MY", "NG", "KE", "GH", "TZ", "UG", "ZM", "ZW",
           "IL", "TH", "VN", "KH", "MM", "JM", "TT", "BB", "BS", "MT"],
}
# SG and MY appear twice above (zh/id and en). First writer wins in the flat
# map built below, and the ORDER of TZ_LANG/REGION_LANG is the tie-break, so
# this is asserted rather than left to chance.
_REGION_FIRST_WINS = {"SG": "zh", "MY": "id"}


def _sanity():
    """Table integrity, checked at import time rather than trusted.

    Two ways this table silently goes wrong: two zones collapsing onto the
    same last-path-segment key (the runtime looks up only that segment), and a
    zone that does not look like a zone at all. Both stop the build.
    """
    seen = {}
    for lang, zones in TZ_LANG.items():
        for z in zones:
            if "/" not in z or z.endswith("/"):
                raise SystemExit(f"ERROR: {z!r} in lang_regions.TZ_LANG[{lang!r}] is not "
                                 f"an Area/City IANA zone name.")
            city = z.rsplit("/", 1)[1]
            if city in seen and seen[city][0] != lang:
                raise SystemExit(
                    f"ERROR: lang_regions.TZ_LANG maps two zones onto the same lookup key "
                    f"{city!r}: {seen[city][1]!r} -> {seen[city][0]} and {z!r} -> {lang}. "
                    f"The runtime keys on the last path segment, so one of them would "
                    f"silently win.")
            seen[city] = (lang, z)
    for region, expect in _REGION_FIRST_WINS.items():
        got = next(l for l, rs in REGION_LANG.items() if region in rs)
        if got != expect:
            raise SystemExit(
                f"ERROR: lang_regions.REGION_LANG resolves {region!r} to {got!r}; the "
                f"documented intent is {expect!r}. Reorder REGION_LANG or update "
                f"_REGION_FIRST_WINS -- do not leave the two disagreeing.")


_sanity()


def tz_table() -> str:
    """The zone table packed for the inline <head> script:
    "ja Tokyo|ko Seoul Pyongyang|...". Parsed once, lazily, at runtime."""
    return "|".join(
        lang + " " + " ".join(z.rsplit("/", 1)[1] for z in zones)
        for lang, zones in TZ_LANG.items())


def region_table() -> str:
    """Same packing for the ISO-3166 region subtags."""
    return "|".join(lang + " " + " ".join(rs) for lang, rs in REGION_LANG.items())


def area_table() -> str:
    """Same packing again — "<lang> <key> <key> ...". It has to be this way
    round because ONE unpack() in the browser reads all three tables; the first
    cut emitted "<area> <lang>" pairs and silently built the map backwards, so
    a Swedish visitor in Europe/Stockholm resolved to nothing instead of to
    English. Grouped by language here so the shape cannot drift again."""
    by_lang = {}
    for area, lang in AREA_DEFAULT.items():
        by_lang.setdefault(lang, []).append(area)
    return "|".join(lang + " " + " ".join(areas) for lang, areas in by_lang.items())


def known_langs() -> set:
    return set(TZ_LANG) | set(REGION_LANG)


if __name__ == "__main__":
    t, r, a = tz_table(), region_table(), area_table()
    print(f"tz     {len(t):5d} bytes, {sum(len(v) for v in TZ_LANG.values()):3d} zones")
    print(f"region {len(r):5d} bytes")
    print(f"area   {len(a):5d} bytes")
    print(f"total  {len(t) + len(r) + len(a):5d} bytes per page")
