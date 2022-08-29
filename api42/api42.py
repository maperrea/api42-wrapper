from datetime import datetime, timedelta
from time import sleep
import requests

class Api42:

    def __init__(self, uid, secret, scope='public', base_url='https://api.intra.42.fr'):
        self.client = requests.Session()
        self.uid = uid
        self.secret = secret
        self.scope = scope
        self.base_url = base_url
        self.next_time_full = datetime.now() + timedelta(seconds=1)
        self.fetch_token()

    def fetch_token(self):
        params = {
                'grant_type': 'client_credentials',
                'client_id': self.uid,
                'client_secret': self.secret,
                'scope': self.scope,
            }
        response = requests.post(self.base_url + '/oauth/token', params=params)
        self.client.headers = {'Authorization': f"Bearer {response.json()['access_token']}"}

    # make a GET call to the api
    # url will be appended to the base_url
    # the key-value pairs for filter, range & page will be transformed as such in the call params:
    #   filter={key1: value1, key2: value2} => "filter[key1]=value1&filter[key2]=value2"
    # sort takes a list and will become: "sort=value1,value2,..."
    # params are raw params (ex: params={'filter[login]': maperrea})
    # will automatically sleep on secondly limit reached
    # will sleep on hourly limit reached if sleep_on_hourly_limit=True
    def get(self, url, filter={}, range={}, page={}, sort=None, params={}, sleep_on_hourly_limit=False, fetch_all=True):
        data = []
        params['page[size]'] = 100
        params['page[number]'] = 1
        for k, v in filter.items():
            params[f"filter[{k}]"] = v
        if sort:
            params["sort"] = ",".join(sort)
        for k, v in range.items():
            params[f"range[{k}]"] = v
        for k, v in page.items():
            params[f"page[{k}]"] = v
        while True:
            response = self.client.get(self.base_url + url, params=params)
            if response.status_code == 400 or response.status_code == 403 or response.status_code == 404:
                code = response.status_code
                try:
                    data = response.json()
                except:
                    data = response._content
                break
            elif response.status_code == 401:
                self.fetch_token()
            elif response.status_code == 429:
                if int(response.headers['retry-after']) == 1: # it's an int so if the secondly limit is hit then it's 1
                    if (next_time_full - datetime.now()).total_seconds() > 0:
                        sleep((next_time_full - datetime.now()).total_seconds())
                elif sleep_on_hourly_limit:
                    #print(f"hourly limit reached, sleeping for {response.headers['retry-after']} seconds")
                    sleep(int(response.headers['retry-after']))
                else:
                    code = response.status_code
                    break
            elif response.status_code == 200:
                if int(response.headers['x-secondly-ratelimit-remaining']) == int(response.headers['x-secondly-ratelimit-limit']) - 1:
                    next_time_full = datetime.now() + timedelta(seconds=1.0 - float(response.headers['x-runtime']))
                r = response.json()
                if type(r) != list:
                    data = r
                    code = 200
                    break
                data += r
                if not fetch_all or len(r) < params['page[size]']:
                    code = 200
                    break
                if int(response.headers['x-secondly-ratelimit-remaining']) == 0:
                    if (next_time_full - datetime.now()).total_seconds() > 0:
                        #print('sleep')
                        sleep((next_time_full - datetime.now()).total_seconds())
                params['page[number]'] += 1

        #python default values are calculated only once and since these are object instances, modifications stay
        filter.clear()
        range.clear()
        page.clear()
        params.clear()
        return (code, data)

