import click
import random

from fn_helper import SpotifyClient


def _shuffle_playlist(playlist):
    """ Checks whether the playlist (matched by uri or name substr)
        has any tracks already in the pool.
    """

    spotify_client = SpotifyClient()
    playlist_id = spotify_client.get_playlist_id(playlist)

    tracks = spotify_client.all_tracks_in_playlist(playlist_id)
    track_order = [t['track']['id'] for t in tracks if t]
    new_track_order = [t['track']['id'] for t in tracks if t]
    random.shuffle(new_track_order)
    for now_at, t in enumerate(new_track_order):
        track_was_at = track_order.index(t)
        if now_at == track_was_at:
            continue
        spotify_client.update_playlist_tracks(
            playlist_id, range_start=track_was_at, range_length=1,
            insert_before=now_at)
        track_order = (
            track_order[:now_at] + [track_order[track_was_at]]
            + track_order[now_at:track_was_at] + track_order[track_was_at+1:])


@click.command()
@click.argument('playlist', nargs=1)
def shuffle_playlist(playlist):
    _shuffle_playlist(playlist)


if __name__ == '__main__':
    shuffle_playlist()
