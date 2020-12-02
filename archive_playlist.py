import click
import shelve

from fn_helper import SpotifyClient
from archives import all_recipes


def track_to_tags_filter(source, track_filter, results):
    for track in source.tracks:
        result = track_filter(track, source)
        if result:
            if not isinstance(result, list):
                result = [result]
            for tag in result:
                results.setdefault(
                    tag, []).append(track.spotify_uri)
    return results


def track_keep_filter(source, track_filter, results):
    return results + [t.spotify_uri for t in source.tracks
                      if track_filter(t, source)]


@click.command()
def archive_playlists():
    spotify_client = SpotifyClient()

    checkpoints = shelve.open('archive_checkpoints.db', writeback=True)

    for Recipe in all_recipes:
        try:
            recipe = Recipe()
            recipe_name = recipe.name or recipe.__class__.__name__

            checkpoint = (checkpoints.get(recipe_name)
                          or getattr(recipe, 'initial_checkpoint', None))
            recipe.source.move_to_checkpoint(checkpoint)
            if isinstance(recipe.target, dict):
                results = {}
                try:
                    while True:
                        source = next(recipe.source)
                        results = track_to_tags_filter(
                            source, recipe.track_filter, results)
                except StopIteration:
                    pass

                for tag, track_uris in results.items():
                    if tag not in recipe.target:
                        continue
                    spotify_client.add_tracks_to_playlist(
                        track_uris, recipe.target[tag])
            else:
                results = []
                try:
                    while True:
                        source = next(recipe.source)
                        results = track_keep_filter(
                            source, recipe.track_filter, results)
                except StopIteration:
                    pass
                spotify_client.add_tracks_to_playlist(
                    results, recipe.target)

            checkpoints[recipe_name] = recipe.sources.checkpoint
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    archive_playlists()
