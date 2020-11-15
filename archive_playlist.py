import itertools

import click

from config import config
from util import id_from_uri, SpotifyClient


@click.command()
@click.argument('playlist', nargs=1)
def archive_playlist(playlist):
    """ Checks whether the playlist (matched by uri or name substr)
        has any tracks already in the pool.
    """

    spotify_client = SpotifyClient()

    members = config['MEMBERS']
    archive_map = {id_from_uri(m['uri']): id_from_uri(m['archive_uri'])
                   for m in members}

    playlist_id = spotify_client.get_playlist_id(playlist)
    tracks = spotify_client.all_tracks_in_playlist(playlist_id)

    # https://developer.spotify.com/documentation/web-api/reference/playlists/add-tracks-to-playlist/
    archiving_tracks = {}
    for track in tracks:
        track_uri = track['track']['uri']
        added_by = track['added_by']['id']
        archive_to = archive_map[added_by]
        archiving_tracks.setdefault(archive_to, []).append(track_uri)

    # Add tracks to each member's archive
    for archive_id, _tracks in archiving_tracks.items():
        spotify_client.add_tracks_to_playlist(_tracks, archive_id)

    # Add all tracks to pool archive
    pool_playlist_id = id_from_uri(config['ALL_POOL'])
    all_track_uris = list(
        itertools.chain.from_iterable(archiving_tracks.values()))
    spotify_client.add_tracks_to_playlist(all_track_uris, pool_playlist_id)


if __name__ == '__main__':
    archive_playlist()
