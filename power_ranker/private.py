import requests
from .exception import AuthorizationError


class PrivateLeague:
    def __init__(self, username=None, password=None):
        self.__username = username
        self.__password = password
        self.__auth_swid = None
        self.__auth_s2 = None

    def authorize(self):
        headers = {'Content-Type': 'application/json'}
        r = requests.post('https://registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/api-key?langPref=en-US',
                           headers=headers)
        if r.status_code != 200 or 'api-key' not in r.headers:
            raise AuthorizationError('failed to get API key')
        api_key = r.headers['api-key']
        headers['authorization'] = 'APIKEY ' + api_key
        payload = {'loginValue': self.__username, 'password': self.__password}
        r = requests.post('https://ha.registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/guest/login?langPref=en-US',
                           headers=headers, json=payload)
        if r.status_code != 200:
            raise AuthorizationError('unable to authorize')
        data = r.json()
        if data['error'] is not None:
            raise AuthorizationError('unable to obtain autorization')
        self.__auth_swid = data['data']['profile']['swid']
        self.__auth_s2   = data['data']['s2']
    
    def get_cookies(self):
      '''Returns s2 an swid'''
      return self.__auth_s2, self.__auth_swid
