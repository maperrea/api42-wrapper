# Python api42 wrapper

Provides the 'Api42' class to interact with school 42's API. \
Takes care of:
* fetching & refreshing the token
* fetching every page of data
* sleeping on request limit reached
* formatting the url & parameters

--- 

## V3 Update

### Init:

New (optional) parameters have been added!
- **uidv3**: your OIDC\_RP\_CLIENT\_ID
- **secretv3**: your OIDC\_RP\_CLIENT\_SECRET
- **username**: your username
- **password**: your password

### Usage of v3 endpoints:

When making a call on a v3 service, transform the url parameter like so: \
```https://<service>.42.fr/api/<version>/<url>``` \
to \
```/v3/<service>/<version>/<url>``` \
The wrapper will take care of the rest \
(inspired by [this notion page](https://www.notion.so/ft42/Intra-V3-API-Gateway-7c26edbdcb1e4b7984f31b617b8f1748?pvs=4), but what's written on it doesn't work, at least for now)

For v2 urls, simply use the ```/v2/<url>``` form

---

### Usage:

#### Init

```python
Api42(uid, secret, uidv3, secretv3, username, password, scope='public', redirect_uri='', sleep_on_hourly_limit=False, pre_hook=None, post_hook=None, hook_token=False)
```
- **uid**: your application's uid
- **secret**: your application's secret
- **uidv3**: your OIDC\_RP\_CLIENT\_ID
- **secretv3**: your OIDC\_RP\_CLIENT\_SECRET
- **username**: your username
- **password**: your password
- **scope**: the scope of the fetched token
- **redirect_uri**: The uri to redirect to after web based authentication
- **sleep\_on\_hourly\_limit**: defines if the client should sleep if the hourly limit is reached. If not, it returns a 429
- **pre_hook**: hook function called right before the actual api call. takes following parameters: ```(method: string, url: string, params: dict)```
- **post_hook**: hook function called right after the actual api call. takes the same parameters as the pre_hook, plus the response object (as returned by ```requests```).
- **hook_token**: if ```True```, hooks are also called when fetching tokens

#### GET

```python
Api42.get(url, filter={}, range={}, page={}, sort=None, params={}, fetch_all=True, token=None)
```

- **url**: the call endpoint
- **filter**: dict, extra url params. key,value pairs become 'filter[key]=value' (v2 only)
- **range**: dict, extra url params. key,value pairs become 'range[key]=value' (v2 only)
- **page**: dict, extra url params. key,value pairs become 'page[key]=value'. default: {'size': 100, 'number': 1} (v2 only)
- **sort**: list, extra url param. becomes 'sort=value1,value2,...' (v2 only)
- **params**: dict, raw extra params. key,value pairs become 'key=value'
- **fetch\_all**: defines if all pages of data should be fetched or not
- **token**: defines another token to use for authentification for this call

=> return value: (status\_code, json)

#### PATCH, PUT, POST

```python
Api42.[patch|put|post](url, json={}, token=None)
```
- **url**: the call endpoint
- **json**: dict, data to be sent in the body a json
- **token**: defines another token to use for authentification for this call

=> return value: (status\_code, json)

#### DELETE
```python
Api42.delete(url, token=None)
```
- **url**: the call endpoint
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

### Web Application Flow

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
