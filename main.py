import os
import json
import httpx
import asyncio
import argparse
import logging
from halo import Halo
from pathlib import Path
from aiofiles import open as aio_open
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


API_BASE = os.getenv("API_BASE", "https://kickchatlogsapi.crime.cx:2096/api")
CHANNELS_FILE = Path("channels.json")


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def get_channels(client):
    resp = await client.get(f"{API_BASE}/get_channels")
    resp.raise_for_status()
    data = resp.json()
    async with aio_open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    return data


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(httpx.HTTPStatusError),
)
async def fetch_page(client, user, channel_id, sort, page):
    resp = await client.get(
        f"{API_BASE}/query",
        params={
            "username": user,
            "databaseName": channel_id,
            "page": page,
            "sort": sort,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data if data else []


async def load_channel(client, name, refresh_cache=False):
    if refresh_cache or not CHANNELS_FILE.exists():
        channels = await get_channels(client)
    else:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            channels = json.load(f)
    for ch in channels:
        if ch.get("username", "").lower() == name.lower():
            return ch
    channels = await get_channels(client)
    for ch in channels:
        if ch.get("username", "").lower() == name.lower():
            return ch
    logging.error(f"Channel not found: {name}")
    exit(1)


async def collect_logs(client, user, channel, sort, log_type, spinner):
    page = 1
    logs_count = 0
    while True:
        spinner.text = f"Fetching page {page}, collected {logs_count} logs..."
        result = await fetch_page(client, user, channel["chatroom_id"], sort, page)
        if not result:
            break
        for entry in result:
            if log_type == "all" or entry.get("metadata", {}).get("type") == log_type:
                yield entry
                logs_count += 1
        page += 1
        await asyncio.sleep(1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--user", required=True, help="Username to fetch logs for"
    )
    parser.add_argument("-c", "--channel", required=True, help="Channel name")
    parser.add_argument(
        "-s", "--sort", choices=["asc", "desc"], default="desc", help="Sort order"
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["all", "message", "reply"],
        default="all",
        help="Log type",
    )
    parser.add_argument(
        "--refresh-cache", action="store_true", help="Force refresh of channel cache"
    )
    args = parser.parse_args()

    if not args.user.strip() or not args.channel.strip():
        logging.error("User and channel names cannot be empty.")
        exit(1)

    print(
        f"Configuration: user={args.user.lower()}, channel={args.channel.lower()}, sort={args.sort}, type={args.type}, refresh_cache={args.refresh_cache}"
    )

    async with httpx.AsyncClient(
        timeout=30.0, limits=httpx.Limits(max_connections=1)
    ) as client:
        channel = await load_channel(client, args.channel, args.refresh_cache)

        dir_path = Path("logs") / channel["username"].lower()
        dir_path.mkdir(parents=True, exist_ok=True)
        out_file = dir_path / f"{args.user.lower()}.json"

        custom_spinner = {
            "interval": 80,
            "frames": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        }
        spinner = Halo(text="Starting log collection...", spinner=custom_spinner)
        spinner.start()
        logs_count = 0
        async with aio_open(out_file, "w", encoding="utf-8") as f:
            async for log in collect_logs(
                client, args.user, channel, args.sort, args.type, spinner
            ):
                await f.write(json.dumps(log, ensure_ascii=False) + "\n")
                logs_count += 1
        spinner.stop_and_persist(
            symbol="✔", text=f"Successfully collected {logs_count} logs"
        )

        logging.info(f"Saved {logs_count} logs to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
