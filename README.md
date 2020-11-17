# 肥宅幫手

## Setup
1. `pip install pipenv`
2. `pipenv shell`
3. `pipenv sync`
4. `cp config.yml.template config.yml`

* For Music League helper please fill in Music League members manifest in config.yml
* For Spotify helper please https://developer.spotify.com/dashboard/applications 
and create an app for yourself. Fill in `CLIENT_ID` and `CLIENT_SECRET` in config.yml

## Authentication
1. At first run, visit `http://127.0.0.1:7000` to complete Spotify auth.
2. Music league parser uses your browser's cookie to workaround with sessions
make sure you never click always allow when granting access to python.

## Usage

### Check Duplication
Check whether a playlist have duplication against the pool.

* `python check_dup.py --help`
* `python check_dup.py {playlist_name}`
* `python check_dup.py {playlist_uri}`

### Archive 
Archive a spotify playlist or a music league round to each members archive and
the pool as well.

* `python archive_playlist.py {playlist_uri}`
* `python archive_playlist.py {music_league_round_url}`

### Round Result
Show round result by summing the votes.

* `python round_result.py {music_league_round_url}`
