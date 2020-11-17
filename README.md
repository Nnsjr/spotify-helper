# 肥宅幫手

## Setup
1. `pip install pipenv`
2. `pipenv shell`
3. `pipenv sync`
4. `cp config.yml.template config.yml`

* For Music League helper please fill in Music League members manifest in config.yml
* For Spotify helper:
    1. Visit https://developer.spotify.com/dashboard/applications 
and create an app for yourself. 
    2. Edit the setting and fill in the callback whitelist URL to be `127.0.0.1:7000`.
    3. Fill in `CLIENT_ID` and `CLIENT_SECRET` in `config.yml`.

## Authentication
1. At first run, run `python setup.py` and visit `http://127.0.0.1:7000` to complete Spotify auth.
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


## Helper Reference

### Spotify Helper

```
from fn_helper import SpotifyClient
spotify_client = SpotifyClient()
```

#### Get playlist ID
* Get ID by playlist URI
```
spotify_client.get_playlist_id(playlist_uri)
```

* Get ID by matching a substring in name
```
spotify_client.get_playlist_id(playlist_name_substr)
```

#### Get all tracks in playlist 
```
spotify_client.all_tracks_in_playlist(playlist_id)
```

#### Add tracks to playlist
```
spotify_client.add_tracks_to_playlist([song_uris], playlist_id)
```

### Music League Helper

```
from fn_helper import MusicLeagueClient
ml_client = MusicLeagueClient()
```
#### Object Definition
https://github.com/Nnsjr/spotify-helper/blob/master/fn_helper/musicleague_util.py#L16
 
#### Parse League
Leave `league_url` to `None` for default league
```
ml_client.parse_league(league_url)
```

#### Parse Round
```
ml_client.parse_round(round_url)
```
