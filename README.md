# Python api42 wrapper

Provides the 'Api42' class to interact with school 42's API. \
Takes care of fetching & refreshing the token, sleeping on request limit reached and formatting the url & parameters

#### Usage:
* Init
```python
Api42(
	uid: your application's uid
	secret: your application's secret
	scope: the scope of the fetched token. default: 'public'
	base_url: the url prepended to the endpoints. default: 'https://api.intra.42.fr'
)
```
* Get
```python
Api42.get(
	url: the call endpoint (appended to the base_url)
	filter: dict, extra url params. key,value pairs become 'filter[key]=value'
	range: dict, extra url params. key,value pairs become 'range[key]=value'
	page: dict, extra url params. key,value pairs become 'page[key]=value'
	sort: list, extra url param. becomes 'sort=value1,value2,...'
	params: dict, raw extra params. key,value pairs become 'key=value'
	sleep_on_hourly_limit: defines if the function should sleep if the hourly limit is reached. default: False
)
```
