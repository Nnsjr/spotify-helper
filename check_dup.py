import click

from config import config
from util import id_from_uri, SpotifyClient


@click.command()
@click.argument('playlist', nargs=1)
def check_dup(playlist):
    """ Checks whether the playlist (matched by uri or name substr)
        has any tracks already in the pool.
    """

    spotify_client = SpotifyClient()
    playlist_id = spotify_client.get_playlist_id(playlist)

    tracks = spotify_client.all_tracks_in_playlist(playlist_id)
    tracks = {t['track']['id']: t['track']['name'] for t in tracks if t}

    pool_playlist_id = id_from_uri(config['ALL_POOL'])
    pool_tracks = spotify_client.all_tracks_in_playlist(pool_playlist_id)
    pool_track_ids = set(t['track']['id'] for t in pool_tracks if t)

    dups = set(tracks.keys()).intersection(pool_track_ids)
    dups = [tracks[t_id] for t_id in dups]
    if dups:
        print("Duplicated tracks found: %s" % dups)
    else:
        print("No duplicated tracks detected.")
    return dups


if __name__ == '__main__':
    check_dup()
