from authlib.integrations.requests_client import OAuth2Session
from authlib.integrations.base_client.errors import MissingTokenError, TokenExpiredError
from datetime import datetime, timedelta
from time import sleep

class Api42:

    def __init__(self, uid, secret, scope='public', base_url='https://api.intra.42.fr'):
        self.client = OAuth2Session(
                client_id=uid,
                client_secret=secret,
                token_endpoint='https://api.intra.42.fr/oauth/token',
                scope=scope,
                )
        self.base_url = base_url
        self.next_time_full = datetime.now() + timedelta(seconds=1)

    # make a GET call to the api
    # url will be appended to the base_url
    # the key-value pairs for filter, range & page will be transformed as such in the call params:
    #   filter={key1: value1, key2: value2} => "filter[key1]=value1&filter[key2]=value2"
    # sort takes a list and will become: "sort=value1,value2,..."
    # params are raw params (ex: params={'filter[login]': maperrea})
    # will automatically sleep on secondly limit reached
    # will sleep on hourly limit reached if sleep_on_hourly_limit=True
    def get(self, url, filter={}, sort=None, range={}, page={}, params={}, sleep_on_hourly_limit=False):
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
            try:
                response = self.client.get(self.base_url + url, params=params)
            except MissingTokenError:
                self.client.fetch_token()
                continue
            except TokenExpiredError:
                self.client.fetch_token()
                continue
            if response.status_code == 400 or response.status_code == 403 or response.status_code == 404:
                return (response.status_code, response.json())
            elif response.status_code == 401:
                self.client.fetch_token()
            elif response.status_code == 429:
                if int(response.headers['retry-after']) == 1: # it's an int so if the secondly limit is hit then it's 1
                    if (next_time_full - datetime.now()).total_seconds() > 0:
                        sleep((next_time_full - datetime.now()).total_seconds())
                elif sleep_on_hourly_limit:
                    #print(f"hourly limit reached, sleeping for {response.headers['retry-after']} seconds")
                    sleep(int(response.headers['retry-after']))
                else:
                    return (response.status_code, response.json())
            elif response.status_code == 200:
                if int(response.headers['x-secondly-ratelimit-remaining']) == int(response.headers['x-secondly-ratelimit-limit']) - 1:
                    next_time_full = datetime.now() + timedelta(seconds=1.0 - float(response.headers['x-runtime']))
                r = response.json()
                if type(r) != list:
                    data = r
                    break
                data += r
                if len(r) < params['page[size]']:
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
        return (200, data)

