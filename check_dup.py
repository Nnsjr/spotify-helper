import click

from config import config
from util import get_url, is_uri, id_from_uri, SpotifyClient

@click.command()
@click.argument('playlist', nargs=1)
def check_dup(playlist):
    """ Checks whether the playlist (matched by uri or name substr)
        has any tracks already in the pool.
    """

    spotify_client = SpotifyClient()

    if is_uri(playlist):
        playlist_id = id_from_uri(playlist)
    else:
        all_playlists = spotify_client.paginate_through(get_url('playlists'))
        matched = next(
            filter(lambda p: playlist in p['name'], all_playlists), {})
        playlist_id = matched.get('id')

    if not playlist_id:
        raise ValueError("No matching playlist found.")

    tracks = spotify_client.paginate_through(
        get_url('tracks', playlist_id=playlist_id),
        params={'offset': 0, 'limit': 100})
    tracks = {t['track']['id']: t['track']['name'] for t in tracks if t}

    pool_playlist_id = id_from_uri(config['ALL_POOL'])
    pool_tracks = spotify_client.paginate_through(
        get_url('tracks', playlist_id=pool_playlist_id))
    pool_track_ids = set(t['track']['id'] for t in pool_tracks if t)

    dups = set(tracks.keys()).intersection(pool_track_ids)
    dups = {t_id: tracks[t_id] for t_id in dups}
    if dups:
        print("Duplicated tracks found: %s" % list(dups.values()))
    else:
        print("No duplicated tracks detected.")
    return dups


if __name__ == '__main__':
    check_dup()
