import re

import pycountry


class QueryInterpretationError(Exception):
    """Raised when a search query cannot be understood."""


def parse_natural_language(query: str) -> dict:
    text = query.lower().strip()

    if not text:
        raise QueryInterpretationError(
            "Unable to interpret query"
        )

    filters = {}
    recognized = False

    mentions_male = bool(
        re.search(r"\b(males?|men|boys?)\b", text)
    )

    mentions_female = bool(
        re.search(r"\b(females?|women|girls?)\b", text)
    )

    if mentions_male and mentions_female:
        recognized = True

    elif mentions_male:
        filters["gender"] = "male"
        recognized = True

    elif mentions_female:
        filters["gender"] = "female"
        recognized = True

    for group in ("child", "teenager", "adult", "senior"):
        if re.search(rf"\b{group}s?\b", text):
            filters["age_group"] = group
            recognized = True

    if re.search(r"\byoung\b", text):
        filters["min_age"] = 16
        filters["max_age"] = 24
        recognized = True

    age_match = re.search(
        r"\b(?:above|over|older than|at least)\s+(\d{1,3})\b",
        text,
    )

    if age_match:
        filters["min_age"] = int(age_match.group(1))
        recognized = True

  
    range_match = re.search(
        r"\bbetween\s+(\d{1,3})\s+and\s+(\d{1,3})\b",
        text,
    )

    if range_match:
        minimum = int(range_match.group(1))
        maximum = int(range_match.group(2))

        if minimum > maximum:
            raise QueryInterpretationError(
                "Unable to interpret query"
            )

        filters["min_age"] = minimum
        filters["max_age"] = maximum
        recognized = True

    for country in pycountry.countries:
        country_name = country.name.lower()

        if re.search(
            rf"\bfrom\s+{re.escape(country_name)}\b",
            text,
        ):
            filters["country_id"] = country.alpha_2
            recognized = True
            break

    country_aliases = {
        "angola": "AO",
        "kenya": "KE",
        "nigeria": "NG",
        "benin": "BJ",
        "ghana": "GH",
        "south africa": "ZA",
        "united states": "US",
        "usa": "US",
        "uk": "GB",
        "united kingdom": "GB",
    }

    if "country_id" not in filters:
        for country_name, country_code in country_aliases.items():
            if re.search(
                rf"\bfrom\s+{re.escape(country_name)}\b",
                text,
            ):
                filters["country_id"] = country_code
                recognized = True
                break

    if not recognized:
        raise QueryInterpretationError(
            "Unable to interpret query"
        )

    return filters