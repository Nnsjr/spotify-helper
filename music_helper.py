import click

from archive_playlists import _archive_playlists
from check_dup import _check_dup
from round_result import _round_result
from setup import setup
from shuffle_playlist import _shuffle_playlist


@click.group()
def music_helper():
    pass


@music_helper.command()
@click.argument('playlist', nargs=1)
def check_dup(playlist):
    _check_dup(playlist)


@music_helper.command()
def archive_playlists():
    _archive_playlists()


@music_helper.command()
@click.argument('round_url', nargs=1)
def round_result(round_url):
    _round_result(round_url)


@music_helper.command()
@click.argument('playlist', nargs=1)
def shuffle_playlist(playlist):
    _shuffle_playlist(playlist)


if __name__ == '__main__':
    setup()
    music_helper()
