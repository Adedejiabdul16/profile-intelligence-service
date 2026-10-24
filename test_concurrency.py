import asyncio
import time

import httpx


BASE_URL = "http://127.0.0.1:8000/api/classify"

NAMES = [
    "azeem",
    "john",
    "mary",
    "david",
    "sarah"
]


async def send_request(client, name):
    start_time = time.perf_counter()

    try:
        response = await client.get(
            BASE_URL,
            params={"name": name},
            timeout=15.0,
        )

        elapsed = time.perf_counter() - start_time

        return {
            "name": name,
            "status_code": response.status_code,
            "time": elapsed,
            "success": response.status_code == 200,
            "response": response.json(),
        }

    except Exception as exc:
        elapsed = time.perf_counter() - start_time

        return {
            "name": name,
            "status_code": None,
            "time": elapsed,
            "success": False,
            "error": str(exc),
        }


async def main():

    print("=" * 60)
    print("STAGE 0 - CONCURRENCY TEST")
    print("=" * 60)

    start_time = time.perf_counter()

    async with httpx.AsyncClient() as client:

        tasks = [
            send_request(client, name)
            for name in NAMES
        ]

        results = await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start_time

    print("\nRESULTS")
    print("-" * 60)

    successful = 0
    failed = 0

    for result in results:

        if result["success"]:
            successful += 1

            print(
                f'{result["name"]:<12} '
                f'SUCCESS '
                f'{result["status_code"]} '
                f'{result["time"]:.3f}s'
            )

        else:
            failed += 1

            print(
                f'{result["name"]:<12} '
                f'FAILED '
                f'{result["time"]:.3f}s'
            )

            if "error" in result:
                print(f'    Error: {result["error"]}')

            if "response" in result:
                print(f'    Response: {result["response"]}')

    print("\nSUMMARY")
    print("-" * 60)

    print(f"Total requests : {len(results)}")
    print(f"Successful     : {successful}")
    print(f"Failed         : {failed}")
    print(f"Total time     : {total_time:.3f}s")

    if failed == 0:
        print("\n✓ All concurrent requests completed successfully.")
    else:
        print("\n✗ Some requests failed.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())