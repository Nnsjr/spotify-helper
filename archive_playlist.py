import click
import shelve

from fn_helper import SpotifyClient
from archives import all_recipes


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
            source = next(recipe.source)
            if isinstance(recipe.target, dict):
                results = {}
                for track in source.tracks:
                    result = recipe.track_filter(track, source)
                    if result:
                        if not isinstance(result, list):
                            result = [result]
                        for tag in result:
                            results.setdefault(
                                tag, []).append(track.spotify_uri)

                for tag, track_uris in results.items():
                    if tag not in recipe.target:
                        continue
                    spotify_client.add_tracks_to_playlist(
                        track_uris, recipe.target[tag])
            else:
                track_uris = [t.spotify_uri for t in source.tracks
                              if recipe.track_filter(t, source)]
                spotify_client.add_tracks_to_playlist(
                    track_uris, recipe.target)

            checkpoints[recipe_name] = recipe.sources.checkpoint
        except Exception as e:
            print(e)
            pass


if __name__ == '__main__':
    archive_playlists()
