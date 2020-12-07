# 肥宅幫手

## Setup

### Development
1. `pip install pipenv`
2. `pipenv shell`
3. `pipenv sync`
4. `cp config.yml.template config.yml`

### Using 
In case you don't have python 3.7 for pipenv you could always fallback using `python -r requirements.txt`

### App and config setup
* For Music League helper please fill in Music League members manifest in `config.yml`
* For Spotify helper:
    1. Visit https://developer.spotify.com/dashboard/applications 
and create an app for yourself. 
    2. Edit the setting and fill in the callback whitelist URL to be `http://127.0.0.1:7000/callback`.
    3. Fill in `CLIENT_ID` and `CLIENT_SECRET` in `config.yml`.

## Authentication
1. At first run, run `python setup.py` and visit `http://127.0.0.1:7000/auth` to complete Spotify auth.
2. Music league parser uses your browser's cookie to workaround with sessions
make sure you never click always allow when granting access to python.

## Usage

### Check Duplication
Check whether a playlist have duplication against the pool.

* `python check_dup.py --help`
* `python check_dup.py {playlist_name}`
* `python check_dup.py {playlist_uri}`

### Archive 
Archive spotify playlists with archive recipes in `arhives/`. For more info
please reference the [Arhive Recipe](#arhive-recipe).

* `python archive_playlists.py`


### Round Result
Show round result by summing the votes.

* `python round_result.py {music_league_round_url}`


## Archive Recipe
Archive recipes placed under `archives/` will be discovered by the command 
`archive_playlists`. They are used as a rule-based archiving instruction to 
keep a record for the tracks in our ML round and Spotify playlists. 

### Incremental collection discovery
The incremental collection discovery is a hard-coded name/title matching 
algorithm to track new rounds/playlists being created under our league or in
our playlist collection. Please follow the naming rule when creating ML rounds
and Spotify playlists:

* Spotify playlists: `MM/DD肥宅聽歌團...`
* Music League round: `MM/DD肥宅聽歌團 - RoundXX - ...`

Each recipe has a checkpoint to track which collection has been archived. 

### Creating an Archive Recipe
To create an Archive Recipe that could be discovered by the command, one must
have it inherit the base class `BaseArchiveRecipe` then set the related fields.

```python 
from .base import BaseArchiveRecipe

class SampleArchiveRecipe(BaseArchiveRecipe):
    pass
```

#### Archive Recipe Fields
* `name`: `str`. Name for your recipe, it also act as the key for checkpoint. 
If the name changes, your progress will also be lost as well.
* `active`: `boolean`. Only active recipes will be triggered.
* `intial_checkpoint`: `str`. The starting collection name of which the archive
process will start with. Please provide the full name to the ML Round or Spotify
Playlist that followed the naming rule listed under
[Incremental collection discovery](#incremental-collection-discovery). If not
provided, the archive process will start with the very first collection
available.
* `source`: Could either be `MLRoundIterator()` or `SpotifyNerdPlaylistIterator()`.
One will iterate through ML Round and the other one will iterate through 
Spotify Playlist with matching name.
* `target`: Could either be 
    * `str`, the ID to a playlist you own. 
    * `dict`, a key-value pair for tags and playlist ID.
* `track_filter(self, track, source)`: `track_filter` is a callable which each
track in the collection will be passed to along with the collection. One can
apply their own rules to decide whether to archive the track and where it will
be archived to. Returns:
    * `boolean`: If you only have a single target you can have this function
       return a boolean which decides whether this track will be archived.
    * `dict`: One can also return a list of tags this track has and they will
       be record accordingly to the target if it were a key-value pair of
       tag and playlist ID.


#### Quick Example
The following example will archive all playlists created after the 11/3 one. 
All the titles with only alphabet and spaces will be recorded into 
playlist `ENGLISH_PLAYLIST_ID`, the others goes to playlist 
`OTHER_LANGUAGE_PLAYLIST_ID`, and all the tracks will be archived in the playlist
`ALL_TRACKS_PLAYLIST_ID` as well.

```python
import re

from fn_helper import SpotifyNerdPlaylistIterator

from .base import BaseArchiveRecipe


class LanguageBasedArchiveRecipe(BaseArchiveRecipe):
    name = "Language Based Spotify Playlist Archiver"
    active = True
    initial_checkpoint = "11/3肥宅聽歌團"
    source = SpotifyNerdPlaylistIterator()
    target = {
        'english': "ENGLISH_PLAYLIST_ID",
        'others': "OTHER_LANGUAGE_PLAYLIST_ID",
        'all': "ALL_TRACKS_PLAYLIST_ID"
    }

    def track_filter(self, track, source):
        english_matcher = re.compile(r"[a-zA-Z ]*")
        return ["english" if english_matcher.match(track.name) else "others",
                "all"]
``` 

## Helper Reference

### Spotify Helper

```python
from fn_helper import SpotifyClient
spotify_client = SpotifyClient()
```

#### Get playlist ID
* Get ID by playlist URI
```python
spotify_client.get_playlist_id(playlist_uri)
```

* Get ID by matching a substring in name
```python
spotify_client.get_playlist_id(playlist_name_substr)
```

#### Get all tracks in playlist 
```python
spotify_client.all_tracks_in_playlist(playlist_id)
```

#### Add tracks to playlist
```python
spotify_client.add_tracks_to_playlist([song_uris], playlist_id)
```

### Music League Helper
```python
from fn_helper import MusicLeagueClient
ml_client = MusicLeagueClient()
```

#### Object Definition
https://github.com/Nnsjr/spotify-helper/blob/master/fn_helper/musicleague_util.py#L16
 
#### Parse League
Leave `league_url` to `None` for default league
```python
ml_client.parse_league(league_url)
```

#### Parse Round
```python
ml_client.parse_round(round_url)
```


## Usage (Deprecated)

### Archive (Deprecated)
Archive a spotify playlist or a music league round to each members archive and
the pool as well.

* `python archive_playlist.py {playlist_uri}`
* `python archive_playlist.py {music_league_round_url}`


