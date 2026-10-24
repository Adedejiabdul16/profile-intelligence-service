import argparse
import asyncio
import csv
import json

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pycountry

from sqlalchemy import select

from app.database import Base, engine, AsyncSessionLocal
from app.models import Profile, generate_uuid7


def load_records(file_path: Path) -> list[dict]:
    """Read profile records from a CSV or JSON file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Seed file not found: {file_path}"
        )

    if file_path.suffix.lower() == ".csv":
        with file_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            return list(csv.DictReader(file))

    if file_path.suffix.lower() == ".json":
        with file_path.open(
            "r", encoding="utf-8-sig"
        ) as file:
            payload = json.load(file)

        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            records = payload.get(
                "profiles", payload.get("data")
            )

            if isinstance(records, list):
                return records

        raise ValueError(
            "JSON must contain a list of profiles, "
            "or a 'profiles'/'data' list."
        )

    raise ValueError(
        "Unsupported seed format. Use .csv or .json."
    )


def parse_created_at(value) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        result = value
    else:
        result = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


def clean_record(record: dict) -> dict:
    """Validate and normalize one seed record."""

    name = str(record.get("name", "")).strip().lower()

    if not name:
        raise ValueError("A seed record has no name.")

    gender = str(record.get("gender", "")).strip().lower()

    if gender not in {"male", "female"}:
        raise ValueError(
            f"Invalid gender for profile {name!r}."
        )

    age = int(record["age"])

    if age < 0:
        raise ValueError(
            f"Invalid age for profile {name!r}."
        )

    age_group = str(
        record.get("age_group", "")
    ).strip().lower()

    expected_group = (
        "child" if age <= 12
        else "teenager" if age <= 19
        else "adult" if age <= 59
        else "senior"
    )

    if age_group and age_group != expected_group:
        raise ValueError(
            f"Incorrect age_group for profile {name!r}."
        )

    country_id = str(
        record.get("country_id", "")
    ).strip().upper()

    if len(country_id) != 2:
        raise ValueError(
            f"country_id must be an ISO alpha-2 code "
            f"for profile {name!r}."
        )

    country = pycountry.countries.get(
        alpha_2=country_id
    )

    if country is None:
        raise ValueError(
            f"Unknown country code {country_id!r} "
            f"for profile {name!r}."
        )

    country_name = str(
        record.get("country_name") or country.name
    ).strip()

    gender_probability = float(
        record["gender_probability"]
    )

    country_probability = float(
        record["country_probability"]
    )

    for field_name, value in (
        ("gender_probability", gender_probability),
        ("country_probability", country_probability),
    ):
        if not 0 <= value <= 1:
            raise ValueError(
                f"{field_name} must be between 0 and 1 "
                f"for profile {name!r}."
            )

    raw_id = record.get("id")
    profile_id = generate_uuid7()

    if raw_id:
        try:
            parsed_id = UUID(str(raw_id))

            if parsed_id.version == 7:
                profile_id = str(parsed_id)

        except ValueError:
            pass

    return {
        "id": profile_id,
        "name": name,
        "gender": gender,
        "gender_probability": gender_probability,
        "sample_size": int(record.get("sample_size") or 0),
        "age": age,
        "age_group": expected_group,
        "country_id": country_id,
        "country_name": country_name,
        "country_probability": country_probability,
        "created_at": parse_created_at(
            record.get("created_at")
        ),
    }


async def seed_database(file_path: Path):
    records = load_records(file_path)

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    inserted = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        for raw_record in records:
            data = clean_record(raw_record)

            existing = await session.scalar(
                select(Profile).where(
                    Profile.name == data["name"]
                )
            )

            if existing:
                skipped += 1
                continue

            session.add(Profile(**data))
            inserted += 1

            if inserted % 100 == 0:
                await session.commit()

        await session.commit()

    print(f"Records read: {len(records)}")
    print(f"New records inserted: {inserted}")
    print(f"Existing records skipped: {skipped}")


async def main():
    parser = argparse.ArgumentParser(
        description="Seed the profile database."
    )

    parser.add_argument(
        "file",
        help="Path to the supplied .json or .csv seed file",
    )

    args = parser.parse_args()

    try:
        await seed_database(Path(args.file))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())