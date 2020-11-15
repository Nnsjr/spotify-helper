# 肥宅幫手

## Setup
1. `pipenv shell`
2. `pipenv sync`
3. `cp config.yml.template config.yml`

## Authentication
1. At first run, visit `http://127.0.0.1:7000` to complete Spotify auth.

## Usage

### Check Duplication
* `python check_dup.py --help`
* `python check_dup.py {playlist_name}`
* `python check_dup.py {playlist_uri}`
