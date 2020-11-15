import re
import shelve
from datetime import datetime, timedelta
from urllib.parse import urlencode
from uuid import uuid4

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


class AuthClient():
    """ AuthClient facilitates oauth access_token retrieving and refreshing.
        Use AuthClient().get_auth_header() to retrieve header for Http header.
    """

    def _handle_token_response(self, token_response):
        """ Handle access_token and refresh access_token response and save
            the attributes to shelve db.
        """
        if not token_response.ok:
            raise ValueError(str(token_response.json()))

        token_response = token_response.json()
        self.token['access_token'] = token_response['access_token']
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
                'client_id': config['APP_CLIENT_ID'],
                'client_secret': config['APP_CLIENT_SECRET'],
                'grant_type': "authorization_code",
                'code': auth_code,
                'redirect_uri': redirect_uri
            }
            token_response = session.post(
                get_url('token'), data=token_request_body)
            self._handle_token_response(token_response)
            self.token['scope'] = set(config['SCOPE'])
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
            'client_id': config['APP_CLIENT_ID'],
        }
        token_response = session.post(
            get_url('token'), data=token_request_body)
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
            if (not self.token.get('access_token')
                    or self.token.get('scope') != set(config['SCOPE'])):
                self._auth_flow(auth_session)
            elif self.token.get('expiry') <= datetime.now():
                self._refresh_access_token(auth_session)
            self.access_token = self.token['access_token']
        finally:
            self.token.close()
            delattr(self, 'token')


class SpotifyClient():
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

    def __init__(self):
        self.client = requests.Session()
        self.client.headers = AuthClient().get_auth_header()
