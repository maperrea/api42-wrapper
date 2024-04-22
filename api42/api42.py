from time import sleep
from base64 import b64encode
from datetime import datetime, timedelta, timezone
import requests
import random
import string
import re

def _detect_v3(func):

    def wrap(self, url, *, token=None, **kwargs):
        if (m := re.match("/v3/([\w\-]*)/(v\d)/(.*)", url)):
            url = f"https://{m.group(1)}.42.fr/api/{m.group(2)}/{m.group(3)}"
            v3 = True
            if not token:
                token = self.tokenv3
        else:
            url = self.base_url + url
            v3 = False
            if not token:
                token = self.token
        return func(self, url, token=token, v3=v3, **kwargs)

    return wrap

class Api42:

    class TokenFetchException(Exception):
        """Exception raised when an error happens during token fetch"""

        def __init__(self, message="An error happened durign token fetch"):
            super().__init__(message)

    def __init__(self, uid='', secret='', uidv3='', secretv3='', username='', password='', totp='', scope='public', redirect_uri='', sleep_on_hourly_limit=False, pre_hook=None, post_hook=None, hook_token=False):
        self.uid = uid
        self.secret = secret
        self.uidv3 = uidv3
        self.secretv3 = secretv3
        self.username = username
        self.password = password
        self.totp = totp
        self.twofa = True if totp else False
        self.scope = scope
        self.base_url = 'https://api.intra.42.fr'
        self.tokenv2_url = 'https://api.intra.42.fr/oauth/token'
        self.tokenv3_url = 'https://auth.42.fr/auth/realms/staff-42/protocol/openid-connect/token'
        self.redirect_uri = redirect_uri
        self.next_time_full = datetime.now() + timedelta(seconds=1)
        self.sleep_on_hourly_limit = sleep_on_hourly_limit
        self.pre_hook = pre_hook
        self.post_hook = post_hook
        self.hook_token = hook_token
        self.states = {}
        self.token = None
        self.tokenv3 = None
        self.refresh_tokenv3= None
        self.refresh_timeout = None 

    #actually make the call to fetch a token
    def _fetch_token(self, v3):
        if v3:
            return self._fetch_token_v3()
        else:
            return self._fetch_token_v2()

    def _fetch_token_v2(self):
        params = {
                'grant_type': 'client_credentials',
                'client_id': self.uid,
                'client_secret': self.secret,
                'scope': self.scope,
            }
        if self.hook_token and self.pre_hook:
            self.pre_hook('POST', self.tokenv2_url,  params)
        response = requests.post(self.tokenv2_url, params=params)
        if self.hook_token and self.post_hook:
            self.post_hook('POST', self.tokenv2_url,  params, response)
        if response.status_code >= 400:
            raise self.TokenFetchException(f"{response.status_code}: {response._content}")
        self.token = response.json()['access_token']
        return self.token


    def _fetch_token_v3(self):
        refresh = False
        if self.refresh_tokenv3 and self.refresh_timeout > datetime.now(timezone.utc):
            refresh = True
        elif self.twofa and not self.totp:
            raise self.TokenFetchException("Two-Factor authentication active and no totp provided and refresh_token timed out or is absent")
        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': b"Basic " + b64encode(bytes(self.uidv3 + ':' + self.secretv3, encoding='utf-8'))
            }
        if refresh:
            params = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_tokenv3,
            }
        else:
            params = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password,
                'totp': self.totp,
            }
        if self.hook_token and self.pre_hook:
            self.pre_hook('POST', self.tokenv3_url, headers | params)
        response = requests.post(self.tokenv3_url, headers=headers, data=params)
        if self.hook_token and self.post_hook:
            self.post_hook('POST', self.tokenv3_url, headers | params, response)
        if response.status_code >= 400:
            raise self.TokenFetchException(f"{response.status_code}: {response._content}")
        self.tokenv3 = response.json()['access_token']
        self.refresh_tokenv3 = response.json()['refresh_token']
        self.refresh_timeout = datetime.now(timezone.utc) + timedelta(seconds=int(response.json()['refresh_expires_in']))
        self.totp = ''
        return self.tokenv3

    def refresh_token(self, totp=''):
        if totp:
            self.twofa = True
            self.totp = totp
        self._fetch_token_v3()

    def _fetch_client_token(self, code, state):
        params = {
                'grant_type': 'authorization_code',
                'client_id': self.uid,
                'client_secret': self.secret,
                'code': code,
                'redirect_uri': self.redirect_uri,
                'state': state,
            }
        if self.hook_token and self.pre_hook:
            self.pre_hook('POST', 'https://api.intra.42.fr/oauth/token',  params)
        response = requests.post('https://api.intra.42.fr/oauth/token', params=params)
        if self.hook_token and self.post_hook:
            self.post_hook('POST', 'https://api.intra.42.fr/oauth/token',  params, response)
        if response.status_code != 200:
            return None
        return response.json()['access_token']

    def authorize(self, key, redirect_uri=None):
        state = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        self.states[key] = state
        return f"https://api.intra.42.fr/oauth/authorize?client_id={self.uid}&redirect_uri={redirect_uri if redirect_uri else self.redirect_uri}&response_type=code&scope={self.scope}&state={state}"

    def authorize_access_token(self, key, code, state):
        if key not in self.states or self.states[key] != state:
            return None
        self.states.pop(key)
        return self._fetch_client_token(code, state)

    def _request(self, method, url, token=None, v3=False, **kwargs):

        while True:
            if self.pre_hook:
                self.pre_hook(method, url, kwargs)
            response = requests.request(method, url, headers={"Authorization": f"Bearer {token}"}, **kwargs)
            if self.post_hook:
                self.post_hook(method, url, kwargs, response)
            status = response.status_code
            if status == 400 or status == 403 or status == 422:
                data = response.json()
                break
            elif status == 404:
                data = response._content
                break
            elif status == 401:
                token = self._fetch_token(v3)
            elif status == 429:
                if int(response.headers['retry-after']) == 1: # it's an int so if the secondly limit is hit then it's 1
                    if (self.next_time_full - datetime.now()).total_seconds() > 0:
                        sleep((self.next_time_full - datetime.now()).total_seconds())
                elif self.sleep_on_hourly_limit:
                    sleep(int(response.headers['retry-after']))
                else:
                    data = response._content
                    break
            elif status >= 400:
                    data = response._content
                    break
            else:
                if not v3 and int(response.headers['x-secondly-ratelimit-remaining']) == int(response.headers['x-secondly-ratelimit-limit']) - 1:
                    self.next_time_full = datetime.now() + timedelta(seconds=1.0 - float(response.headers['x-runtime']))
                try:
                    data = response.json()
                except:
                    data = response._content
                break

        return (status, data)

    def _getv2(self, url, *, filter={}, range={}, page={}, sort=None, params={}, fetch_all=True, token=None):
        data = []
        _params = params.copy()
        _params['page[size]'] = 100
        _params['page[number]'] = 1
        for k, v in filter.items():
            _params[f"filter[{k}]"] = v
        if sort:
            _params["sort"] = ",".join(sort)
        for k, v in range.items():
            _params[f"range[{k}]"] = v
        for k, v in page.items():
            _params[f"page[{k}]"] = v
        while True:
            status, r = self._request("GET", url, params=_params, token=token, v3=False)
            if status >= 200 and status <= 299:
                if type(r) != list:
                    data = r
                    break
                data += r
                if not fetch_all or len(r) < _params['page[size]']:
                    break
                _params['page[number]'] += 1
            else:
                data = r
                break
        return (status, data)
    
    def _getv3(self, url, *, params={}, fetch_all=True, token=None):
        data = []
        _params = {'size': 100, 'page': 1}
        for k, v in params.items(): #allows override of size/number
            _params[k] = v
        while True:
            status, r = self._request("GET", url, params=_params, token=token, v3=True)
            if status >= 200 and status <= 299:
                if 'items' not in r:
                    data = r
                    break
                data += r['items']
                if not fetch_all or r['page'] == r['pages']:
                    break
                _params['page'] += 1
            else:
                data = r
                break
        return (status, data)

    @_detect_v3
    def get(self, url, *, filter={}, range={}, page={}, sort=None, params={}, fetch_all=True, token=None, v3=False):
        if v3:
            return self._getv3(url, params=params, fetch_all=fetch_all, token=token)
        else:
            return self._getv2(url, filter=filter, range=range, page=page, sort=sort, params=params, fetch_all=fetch_all, token=token)

    @_detect_v3
    def patch(self, url, *, json={}, token=None, v3=False):
        status, data = self._request("PATCH", url, json=json, token=token, v3=v3)
        return (status, data)

    @_detect_v3
    def put(self, url, *, json={}, token=None, v3=False):
        status, data = self._request("PUT", url, json=json, token=token, v3=v3)
        return (status, data) 

    @_detect_v3
    def post(self, url, *, json={}, token=None, v3=False):
        status, data = self._request("POST", url, json=json, token=token, v3=v3)
        return (status, data)

    @_detect_v3
    def delete(self, url, *, json={}, token=None, v3=False):
        status, data = self._request("DELETE", url, json=json, token=token, v3=v3)
        return (status, data)
