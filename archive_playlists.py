import shelve
from itertools import chain

import click

from fn_helper import SpotifyClient
from archives import all_recipes


def _archive_playlists():
    spotify_client = SpotifyClient()

    checkpoints = shelve.open('archive_checkpoints.db', writeback=True)

    for Recipe in all_recipes:
        try:
            recipe = Recipe()

            if not recipe.active:
                continue
            recipe_name = recipe.name

            checkpoint = (checkpoints.get(recipe_name)
                          or getattr(recipe, 'initial_checkpoint', None))
            recipe.source.move_to_checkpoint(checkpoint)

            results = {}
            while True:
                try:
                    source = next(recipe.source)
                except StopIteration:
                    break
                for track in source.tracks:
                    result = recipe.track_filter(track, source)
                    if not result:
                        continue

                    if not isinstance(result, list):
                        result = [result]
                    for tag in result:
                        results.setdefault(
                            tag, []).append(track.spotify_uri)

            if isinstance(recipe.target, dict):
                for tag, track_uris in results.items():
                    if tag not in recipe.target:
                        continue
                    spotify_client.add_tracks_to_playlist(
                        track_uris, recipe.target[tag])
            else:
                spotify_client.add_tracks_to_playlist(
                    list(chain.from_iterable(results.values())), recipe.target)

            checkpoints[recipe_name] = recipe.source.checkpoint
        except Exception as e:
            print(e)
            pass

    checkpoints.sync()
    checkpoints.close()


@click.command()
def archive_playlists():
    _archive_playlists()


if __name__ == '__main__':
    archive_playlists()
