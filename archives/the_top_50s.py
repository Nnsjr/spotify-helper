from fn_helper import MLRoundIterator

from .base import BaseArchiveRecipe


class MLTop50PercentArchiveRecipe(BaseArchiveRecipe):
    name = "MusicLeague_top_rankers"
    active = False
    initial_checkpoint = "11/17肥宅聽歌團 - Round 10 - 凌晨四點想睡但真的睡不著"  # noqa
    source = MLRoundIterator()
    target = "6Ug5S08Pyduh5rfPVKME5m"

    def track_filter(self, track, source):
        round_total = sum(dict(source.result.vote_count).values())
        average_score = round_total / len(source.tracks)
        return track.score >= average_score
