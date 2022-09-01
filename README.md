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
Api42(uid, secret, scope='public', base_url='https://api.intra.42.fr', sleep_on_hourly_limit=False)
```
- **uid**: your application's uid
- **secret**: your application's secret
- **scope**: the scope of the fetched token
- **base\_url**: the url prepended to the endpoints
- **sleep\_on\_hourly\_limit**: defines if the client should sleep if the hourly limit is reached. If not, it returns a 429

#### Get

```python
Api42.get(url, filter={}, range={}, page={}, sort=None, params={}, fetch_all=True, token=None)
```

- **url**: the call endpoint (appended to the base\_url)
- **filter**: dict, extra url params. key,value pairs become 'filter[key]=value'
- **range**: dict, extra url params. key,value pairs become 'range[key]=value'
- **page**: dict, extra url params. key,value pairs become 'page[key]=value'. default: {'size': 100, 'number': 1}
- **sort**: list, extra url param. becomes 'sort=value1,value2,...'
- **params**: dict, raw extra params. key,value pairs become 'key=value'
- **fetch\_all**: defines if all pages of data should be fetched or not
- **token**: defines another token to use for authentification for this call

=> return value: (status\_code, json)

#### PATCH, PUT, POST

```python
Api42.[patch|put|post](url, json={}, token=None)
```
- **url**: the call endpoint (appended to the base\_url)
- **json**: dict, data to be sent in the body a json
- **token**: defines another token to use for authentification for this call

=> return value: (status\_code, json)

#### DELETE
```python
Api42.delete(url, token=None)
```
- **url**: the call endpoint (appended to the base\_url)
- **token**: defines another token to use for authentification for this call

=> return value: (status\_code, json)

#### Example

```python
>>> from api42 import Api42
>>> client = Api42(UID, SECRET)
>>> status, data = client.get('/v2/cursus/21/users', filter={'primary_campus_id': 21})
>>> len(data)
575
```

### Future improvements

- Add functions to help with the web application flow
