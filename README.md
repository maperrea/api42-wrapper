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

#### GET

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

### Web Applications Flow

#### authorize
```python
Api42.authorize(key, redirect_uri=None)
```

- **key**: key uniquely identifying a user. ex for django: ```request.session.session_key```
- **redirect_uri**: custom redirect uri to use for this call

=> return value: url to send to user for the oauth2 dialog

#### authorize\_access\_token
```python
Api42.authorize_access_token(key, code, state)
```

- **key**: key uniquely identifying a user. Same as for authorize. Used for state verification.
- **code**: the code provided by the intra redirect
- **state**: the state provided by the intra redirect

=> return value: the user's access token to use for api calls

#### Example

- for django:
```python
def authenticate(request):
    return redirect(api42.authorize(key=request.session.session_key))

def authorize(request):
    token = api42.authorize_access_token(key=request.session.session_key, code=request.GET.get('code', default=None), state=request.GET.get('state', default=None))
```
