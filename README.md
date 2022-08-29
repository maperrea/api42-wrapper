# Python api42 wrapper

Provides the 'Api42' class to interact with school 42's API. \
Takes care of:
* fetching & refreshing the token
* fetching every page of data
* sleeping on request limit reached
* formatting the url & parameters

### Usage:

#### Init

```python
Api42(uid, secret, scope='public', base_url='https://api.intra.42.fr')
```
- uid: your application's uid
- secret: your application's secret
- scope: the scope of the fetched token
- base\_url: the url prepended to the endpoints

#### Get

```python
Api42.get(self, url, filter={}, range={}, page={}, sort=None, params={}, sleep_on_hourly_limit=False, fetch_all=True)
```

- url: the call endpoint (appended to the base\_url)
- filter: dict, extra url params. key,value pairs become 'filter[key]=value'
- range: dict, extra url params. key,value pairs become 'range[key]=value'
- page: dict, extra url params. key,value pairs become 'page[key]=value'. default: {'size': 100, 'number': 1}
- sort: list, extra url param. becomes 'sort=value1,value2,...'
- params: dict, raw extra params. key,value pairs become 'key=value'
- sleep\_on\_hourly\_limit: defines if the function should sleep if the hourly limit is reached
- fetch\_all: defines if all pages of data should be fetched or not

* return value: (status\_code, json)

#### Example

```python
>>> from api42 import Api42
>>> client = Api42(UID, SECRET)
>>> status, data = client.get('/v2/users/maperrea/projects_users', filter={'status': 'finished', 'occurence': 0})
```
