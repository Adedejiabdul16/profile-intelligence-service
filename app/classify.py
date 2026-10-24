import httpx
from datetime import datetime, timezone

GENDERIZE_URL = "https://api.genderize.io"


async def classify_name(name: str):

    try:

        async with httpx.AsyncClient() as client:

            response = await client.get(GENDERIZE_URL, params={"name": name})

            response.raise_for_status()
            result = response.json()

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
                f"Genderize returned an HTTP error: {exc.response.status_code}"
            ) from exc

    except httpx.RequestError as exc:
        raise RuntimeError("Unable to connect to Genderize"
            ) from exc

    except ValueError as exc:
            raise RuntimeError(
                "Genderize returned an invalid response"
            ) from exc


    gender = result["gender"]
    probability = result["probability"]
    sample_size = result["count"]

    if gender is None or sample_size == 0:
        return {
            "status": "error",
            "message": "No prediction available for the provided name"
        }

    is_confident = probability >= 0.7 and sample_size >= 100
    processed_at = datetime.now(timezone.utc)

    return {
            "status": "success",
            "data": {
                "name": name,
                "gender": gender,
                "probability": probability,
                "sample_size": sample_size,
                "is_confident": is_confident,
                "processed_at": processed_at
            }
        }