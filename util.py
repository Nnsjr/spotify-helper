import re
import shelve
import os.path
from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse
from uuid import uuid4

from bs4 import BeautifulSoup
import browser_cookie3
import requests
from flask import Flask, redirect, request

from config import config

URLS = {
    'auth': 'https://accounts.spotify.com/authorize',
    'token': 'https://accounts.spotify.com/api/token',
    'playlists': 'https://api.spotify.com/v1/me/playlists',
    'playlist': 'https://api.spotify.com/v1/playlists/{playlist_id}',
    'tracks': 'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
}
MUSIC_LEAGUE_DOMAIN = 'musicleague.app'


def remove_prefix(text, prefix):
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):]
    return text


def get_url(endpoint, **kwargs):
    """ Get endpoint url, and format it with ids.
    """
    return URLS[endpoint].format(**kwargs)


def id_from_uri(resource):
    """ Extract id from uri, refer to:
        https://developer.spotify.com/documentation/web-api/#spotify-uris-and-ids
    """
    return resource.split(':')[-1]


def is_uri(resource):
    """ Check resource is in uri format.
    """
    return bool(re.match(r"^(\w+):(\w+):([0-9a-zA-Z])+$", resource))


def chunk_gen(seq, size=100):
    for pos in range(0, len(seq), size):
        yield(seq[pos:pos + size])


class AuthClient:
    """ AuthClient facilitates oauth access_token retrieving and refreshing.
        Use AuthClient().get_auth_header() to retrieve header for Http header.
    """

    @property
    def _get_authorization_header(self):
        login = "{}:{}".format(config['APP_CLIENT_ID'],
                               config['APP_CLIENT_SECRET']).encode('ascii')
        return {
            "Authorization": "Basic %s" % b64encode(login).decode('utf-8')
        }

    def _handle_token_response(self, token_response):
        """ Handle access_token and refresh access_token response and save
            the attributes to shelve db.
        """
        if not token_response.ok:
            raise ValueError(str(token_response.json()))

        token_response = token_response.json()
        self.token['access_token'] = token_response['access_token']
        self.token['scope'] = set(token_response['scope'].split(' '))
        if 'refresh_token' in token_response:
            self.token['refresh_token'] = token_response['refresh_token']
        expires_in = token_response['expires_in']
        self.token['expiry'] = datetime.now() + timedelta(seconds=expires_in)

    def _run_oauth_client(self, session):
        """ Run a Flask App to handle Spotify OAuth Callback.
        """
        app = Flask('OAuth Client')
        host = config['OAUTH_CLIENT_HOST']
        port = config['OAUTH_CLIENT_PORT']
        redirect_uri = f"http://{host}:{port}/callback"

        @app.route('/auth')
        def authorization_code():
            """ Redirects /auth to the authorization code webpage.
            """
            params = {
                'client_id': config['APP_CLIENT_ID'],
                'response_type': "code",
                'redirect_uri': redirect_uri,
                'state': session.session_id,
                'scope': ' '.join(config['SCOPE'])
            }
            return redirect('{}?{}'.format(get_url('auth'), urlencode(params)))

        @app.route('/callback')
        def callback():
            """ Handles authorization code callback and later calls
                access_token get.
            """
            error = request.args.get('error')
            if error:
                raise ValueError(error)

            auth_code = request.args.get('code')

            token_request_body = {
                'grant_type': "authorization_code",
                'code': auth_code,
                'redirect_uri': redirect_uri
            }
            token_response = session.post(
                get_url('token'), data=token_request_body,
                headers=self._get_authorization_header)
            self._handle_token_response(token_response)
            shutdown = request.environ.get('werkzeug.server.shutdown')
            if not shutdown:
                raise RuntimeError("Access code succesfully retrieved.")
            shutdown()
            return 'Well, hello there!'

        app.run(host=host, port=port)

    def _refresh_access_token(self, session):
        """ Refreshes access_token and saves the new access_token,
            refresh_token, expiry to shelve db.
        """
        token_request_body = {
            'grant_type': "refresh_token",
            'refresh_token': self.token['refresh_token'],
        }
        token_response = session.post(
            get_url('token'), data=token_request_body,
            headers=self._get_authorization_header)
        self._handle_token_response(token_response)

    def _auth_flow(self, session):
        """ Helper function to start the auth flow for the user. Consider
            popping a window in web server.
        """
        host = config['OAUTH_CLIENT_HOST']
        port = config['OAUTH_CLIENT_PORT']
        auth_uri = f"http://{host}:{port}/auth"
        print(f"Visit {auth_uri} and complete the authorization flow")
        self._run_oauth_client(session)

    def get_auth_header(self):
        """ Get authentication header dict for spotify request session.
        """
        return {'Authorization': "Bearer %s" % self.access_token}

    def __init__(self):
        try:
            self.token = shelve.open('oauth2_token.db', writeback=True)
            auth_session = requests.Session()
            auth_session.session_id = uuid4().hex
            if not self.token.get('access_token'):
                self._auth_flow(auth_session)
            elif self.token.get('expiry') <= datetime.now():
                self._refresh_access_token(auth_session)
            self.access_token = self.token['access_token']
        finally:
            self.token.close()
            delattr(self, 'token')


class SpotifyClient:
    def handle_request(self, method, *args, **kwargs):
        """ Handles HTTP response erros.
            TODO: Better handler
        """
        resp = method(*args, **kwargs)
        result = resp.json()
        if not resp.ok:
            raise ValueError(str(result))
        return result

    def paginate_through(self, url, params=None):
        """ Paginates through a paginated object listing with the starter url.
        """
        results = []
        if params is None:
            params = {'limit': 50}
        while url:
            resp = self.handle_request(
                self.client.get, url, params=params)
            results.extend(resp['items'])
            url = resp.get('next')
        return results

    def get_playlist_id(self, playlist):
        # If in URI format
        if is_uri(playlist):
            playlist_id = id_from_uri(playlist)
        # If in name format
        else:
            all_playlists = self.paginate_through(get_url('playlists'))
            matched = next(
                filter(lambda p: playlist in p['name'], all_playlists), {})
            playlist_id = matched.get('id')
        if not playlist_id:
            raise ValueError("No matching playlist found.")
        return playlist_id

    def all_tracks_in_playlist(self, playlist_id):
        return self.paginate_through(
            get_url('tracks', playlist_id=playlist_id),
            params={'offset': 0, 'limit': 100})

    def add_tracks_to_playlist(self, tracks, playlist_id):
        for chunk in chunk_gen(tracks):
            self.handle_request(
                self.client.post,
                get_url('tracks', playlist_id=playlist_id),
                params={'uris': ','.join(chunk)})

    def __init__(self):
        self.client = requests.Session()
        self.client.headers = AuthClient().get_auth_header()


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
class MLRound:
    title: str
    tracks: list

    @property
    def round_result(self):
        result = {}
        for t in self.tracks:
            result[t.submitted_by] = result.get(t.submitted_by, 0) + t.score
        return sorted(result.items(), lambda x: x[1], reverse=True)


class MusicLeagueClient:

    @staticmethod
    def _extract_classes_string(parent, *names):
        return [parent.find(class_=n).string for n in names]

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

        return MLRound(title=title, tracks=tracks)

    def __init__(self):
        browser_name = config['BROWSER_NAME'].lower()
        cookie_reader = getattr(browser_cookie3, browser_name)
        cookies = cookie_reader(domain_name=MUSIC_LEAGUE_DOMAIN)

        self.ml_session = requests.Session()
        self.ml_session.cookies = cookies
