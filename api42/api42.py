from datetime import datetime, timedelta
from time import sleep
import requests

class Api42:

    #TODO webapp flow

    def __init__(self, uid, secret, scope='public', base_url='https://api.intra.42.fr', sleep_on_hourly_limit=False):
        self.client = requests.Session()
        self.uid = uid
        self.secret = secret
        self.scope = scope
        self.base_url = base_url
        self.next_time_full = datetime.now() + timedelta(seconds=1)
        self.sleep_on_hourly_limit = sleep_on_hourly_limit
        self._fetch_token()

    #actually make the call to fetch a token
    def _fetch_token(self):
        params = {
                'grant_type': 'client_credentials',
                'client_id': self.uid,
                'client_secret': self.secret,
                'scope': self.scope,
            }
        response = requests.post(self.base_url + '/oauth/token', params=params)
        self.token = response.json()['access_token']
        self.set_token(response.json()['access_token'])

    #set the header to another token (ex: webapp flow)
    def set_token(self, token):
        self.client.headers = {"Authorization": f"BEARER {token}"}

    #reset to the original token, does not make a call (if token has expired it will simply 401)
    def reset_token(self):
        self.set_token(self.token)

    def _request(self, method, url, token=None, **kwargs):
        if token:
            self.set_token(token)

        while True:
            response = self.client.request(method, self.base_url + url, **kwargs)
            status = response.status_code
            if status == 400 or status == 403 or status == 422:
                data = response.json()
                break
            elif status == 404:
                data = response._content
                break
            elif status == 401:
                self._fetch_token()
            elif status == 429:
                if int(response.headers['retry-after']) == 1: # it's an int so if the secondly limit is hit then it's 1
                    if (self.next_time_full - datetime.now()).total_seconds() > 0:
                        sleep((self.next_time_full - datetime.now()).total_seconds())
                elif self.sleep_on_hourly_limit:
                    sleep(int(response.headers['retry-after']))
                else:
                    break
            else:
                if int(response.headers['x-secondly-ratelimit-remaining']) == int(response.headers['x-secondly-ratelimit-limit']) - 1:
                    self.next_time_full = datetime.now() + timedelta(seconds=1.0 - float(response.headers['x-runtime']))
                try:
                    data = response.json()
                except:
                    data = response._content
                break

        if token:
            self.reset_token()

        return (status, data)

    def get(self, url, filter={}, range={}, page={}, sort=None, params={}, fetch_all=True, Token=None):
        data = []
        _params = params
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
            status, r = self._request("GET", url, params=_params)
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

    def patch(self, url, json={}, token=None):
        status, data = self._request("PATCH", url, json=json, token=None)
        return (status, data)

    def put(self, url, json={}, token=None):
        status, data = self._request("PUT", url, json=json, token=None)
        return (status, data)

    def post(self, url, json={}, token=None):
        status, data = self._request("POST", url, json=json, token=None)
        return (status, data)

    def delete(self, url, token=None):
        status, data = self._request("DELETE", url, token=None)
        return (status, data)
