import os.path
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import browser_cookie3
import requests

from .util import remove_prefix
from .config import config

MUSIC_LEAGUE_DOMAIN = 'musicleague.app'


@dataclass
class MLTrack:
    name: str
    img_url: str
    link: str
    artist: str
    submitted_by: str
    comments: dict
    upvotes: list

    @property
    def score(self):
        return sum(self.upvotes.values())

    @property
    def spotify_id(self):
        return os.path.split(urlparse(self.link).path)[1]

    @property
    def spotify_uri(self):
        return f"spotify:track:{self.spotify_id}"


@dataclass
class MLRoundResult:
    title: str
    tracks: list

    @property
    def vote_count(self):
        result = {}
        for t in self.tracks:
            result[t.submitted_by] = result.get(t.submitted_by, 0) + t.score
        return sorted(result.items(), key=lambda x: x[1], reverse=True)


@dataclass
class MLRound:
    title: str
    playlist_link: str
    result: MLRoundResult


@dataclass
class MLLeague:
    title: str
    completed_rounds: list


class MusicLeagueClient:

    @staticmethod
    def _extract_classes_string(parent, *names):
        return [parent.find(class_=n).string for n in names]

    def parse_league(self, url=None):
        if not url:
            url = f'https://{MUSIC_LEAGUE_DOMAIN}/l/{config["MUSIC_LEAGUE_ID"]}/'  # noqa
        resp = self.ml_session.get(url)
        if not resp.ok:
            raise ValueError(resp.text)

        league_dom = BeautifulSoup(resp.text, 'html.parser')
        title = league_dom.find(class_="league-title").string

        completed_rounds = []
        completed_rounds_dom = league_dom.find_all(class_="round-bar complete")
        for rnd in completed_rounds_dom:
            round_title = league_dom.find(class_="round-title").string
            playlist_link = rnd.find(class_="playlist").parent['href']
            result_link = rnd.find(class_="results").parent['href']
            completed_rounds.append(
                MLRound(
                    title=round_title, playlist_link=playlist_link,
                    result=self.parse_round(
                        f'https://{MUSIC_LEAGUE_DOMAIN}{result_link}'))
            )
        return MLLeague(title=title, completed_rounds=completed_rounds)

    def parse_round(self, url):
        resp = self.ml_session.get(url)
        if not resp.ok:
            raise ValueError(resp.text)
        bs = BeautifulSoup(resp.text, 'html.parser')

        title = bs.find(class_="round-title").string

        tracks = []
        track_doms = bs.find_all(class_="song")
        for track_dom in track_doms:
            song_info = track_dom.find(class_="song-info")
            img_url = track_dom.img['src']
            name, artist, submitted_by = (
                self._extract_classes_string(
                    song_info, "name", "artist", "submitter"))
            link = song_info.find(class_="name")['href']
            submitted_by = remove_prefix(submitted_by, "submitted by ")
            artist = remove_prefix(artist, "by ")

            comment_doms = track_dom.find_all(class_="comment")
            comments = {}
            for comment_dom in comment_doms:
                commenter = remove_prefix(
                    comment_dom.find(class_="commenter").string, "- ")
                comment = comment_dom.next_element
                comments[commenter] = comment

            upvote_doms = track_dom.find_all(class_="upvote")
            upvotes = {}
            for upvote in upvote_doms:
                score, voter = self._extract_classes_string(
                    upvote, "vote-count", "voter")
                score = int(score)
                upvotes[voter] = score

            track = MLTrack(
                name=name, img_url=img_url, submitted_by=submitted_by,
                link=link, artist=artist, comments=comments, upvotes=upvotes)
            tracks.append(track)

        return MLRoundResult(title=title, tracks=tracks)

    def __init__(self):
        browser_name = config['BROWSER_NAME'].lower()
        cookie_reader = getattr(browser_cookie3, browser_name)
        cookies = cookie_reader(domain_name=MUSIC_LEAGUE_DOMAIN)

        self.ml_session = requests.Session()
        self.ml_session.cookies = cookies
