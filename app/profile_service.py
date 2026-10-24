import asyncio

import httpx
import pycountry


GENDERIZE_URL = "https://api.genderize.io"
AGIFY_URL = "https://api.agify.io"
NATIONALIZE_URL = "https://api.nationalize.io"


class ExternalAPIError(Exception):
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(
            f"{service_name} returned an invalid response"
        )


async def fetch_api_data(
    client: httpx.AsyncClient,
    service_name: str,
    url: str,
    name: str,
) -> dict:
    try:
        response = await client.get(
            url,
            params={"name": name},
        )
        response.raise_for_status()

        data = response.json()

    except (httpx.HTTPError, ValueError) as exc:
        raise ExternalAPIError(service_name) from exc

    if not isinstance(data, dict):
        raise ExternalAPIError(service_name)

    return data


def classify_age_group(age: int) -> str:
    if 0 <= age <= 12:
        return "child"

    if 13 <= age <= 19:
        return "teenager"

    if 20 <= age <= 59:
        return "adult"

    if age >= 60:
        return "senior"

    raise ExternalAPIError("Agify")


def get_country_name(country_id: str) -> str:
    """Convert an ISO country code into its full country name."""

    country = pycountry.countries.get(
        alpha_2=country_id.upper()
    )

    if country is None:
        raise ExternalAPIError("Nationalize")

    return country.name


async def enrich_profile(name: str) -> dict:
    """Fetch demographic data from all three APIs concurrently."""

    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        results = await asyncio.gather(
            fetch_api_data(
                client, "Genderize", GENDERIZE_URL, name
            ),
            fetch_api_data(
                client, "Agify", AGIFY_URL, name
            ),
            fetch_api_data(
                client, "Nationalize", NATIONALIZE_URL, name
            ),
            return_exceptions=True,
        )

    for result in results:
        if isinstance(result, Exception):
            raise result

    gender_data, age_data, nationality_data = results

    gender = gender_data.get("gender")
    probability = gender_data.get("probability")
    sample_size = gender_data.get("count")

    if (
        gender not in ("male", "female")
        or not isinstance(probability, (int, float))
        or isinstance(probability, bool)
        or not 0 <= probability <= 1
        or not isinstance(sample_size, int)
        or isinstance(sample_size, bool)
        or sample_size <= 0
    ):
        raise ExternalAPIError("Genderize")

    age = age_data.get("age")

    if (
        not isinstance(age, int)
        or isinstance(age, bool)
        or age < 0
    ):
        raise ExternalAPIError("Agify")

    age_group = classify_age_group(age)

    countries = nationality_data.get("country")

    if not isinstance(countries, list) or not countries:
        raise ExternalAPIError("Nationalize")

    valid_countries = [
        country
        for country in countries
        if (
            isinstance(country, dict)
            and isinstance(country.get("country_id"), str)
            and isinstance(
                country.get("probability"), (int, float)
            )
            and not isinstance(country.get("probability"), bool)
            and 0 <= country["probability"] <= 1
        )
    ]

    if not valid_countries:
        raise ExternalAPIError("Nationalize")

    most_likely_country = max(
        valid_countries,
        key=lambda country: country["probability"],
    )

    country_id = most_likely_country["country_id"].upper()

    return {
        "gender": gender,
        "gender_probability": float(probability),
        "sample_size": sample_size,
        "age": age,
        "age_group": age_group,
        "country_id": country_id,
        "country_name": get_country_name(country_id),
        "country_probability": float(
            most_likely_country["probability"]
        ),
    }