from fn_helper import config, MLRoundIterator, SpotifyNerdPlaylistIterator
from fn_helper.util import id_from_uri

from .base import BaseArchiveRecipe


class MLArchiveRecipe(BaseArchiveRecipe):
    name = "MusicLeague_archiver"
    active = False
    initial_checkpoint = "11/3肥宅聽歌團 - Round 8 - 我知道你沒聽過，但希望你會喜歡"  # noqa
    source = MLRoundIterator()
    target = {
        m['ml_handle']: id_from_uri(m['archive_uri'])
        for m in config["MEMBERS"] if 'ml_handle' in m}
    target["all"] = config["ALL_POOL"]

    def track_filter(self, track, source):
        return [track.submitted_by, "all"]


class SpotifyArchiveRecipe(BaseArchiveRecipe):
    name = "Spotify_nerd_archiver"
    active = False
    initial_checkpoint = "11/06肥宅聽歌團"
    source = SpotifyNerdPlaylistIterator()
    target = {
        id_from_uri(m['uri']): id_from_uri(m['archive_uri'])
        for m in config["MEMBERS"]}
    target["all"] = config["ALL_POOL"]

    def track_filter(self, track, source):
        return [track.submitted_by, "all"]
