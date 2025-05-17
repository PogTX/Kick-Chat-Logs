# Kick Chat Logs Scraper

A Python script that fetches chat logs from Kick channels and saves them as JSON files.

## Features

- Fetch chat logs for a specific **user** in a chosen **channel**
- Control:

  - **Sort order:** `asc` | `desc`
  - **Log type:** `all` | `message` | `reply`
  - **Cache:** optionally refresh the channel cache

- Logs are written to `logs/<channel>/<user>.json`
- Real-time progress indicator in the terminal

## Requirements

- **Python ≥ 3.8**

## Installation

```bash
git clone https://github.com/PogTX/kick-chat-logs-scraper.git
cd kick-chat-logs-scraper
pip install -r requirements.txt
```

## Usage

```bash
python script.py -u <username> -c <channel> [options]
```

### Options

| Flag              | Description                            | Required | Default |
| ----------------- | -------------------------------------- | -------- | ------- |
| `-u`, `--user`    | Username                               | **Yes**  | —       |
| `-c`, `--channel` | Channel name                           | **Yes**  | —       |
| `-s`, `--sort`    | Sort order (`asc` / `desc`)            | No       | `desc`  |
| `-t`, `--type`    | Log type (`all` / `message` / `reply`) | No       | `all`   |
| `--refresh-cache` | Refresh channel cache                  | No       | `False` |

## Examples

```bash
# Fetch all logs for ChristopherColumbus in IcePoseidon
python script.py -u ChristopherColumbus -c IcePoseidon

# Fetch only message logs for John in xQc, sorted ascending
python script.py -u John -c xQc -s asc -t message
```

## Output

- Logs are saved to `logs/<channel>/<user>.json`
- Terminal displays progress (e.g., `Fetching page 1, collected 0 logs...`)
