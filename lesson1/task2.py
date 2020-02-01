import json
import requests
from requests.auth import HTTPBasicAuth

if __name__ == '__main__':
    user_name = input('Insert github user name: ')
    user_pwd = input('Insert github user password: ')

    url = 'https://api.github.com'
    request = f'/user'

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get(url+request, headers=headers, auth=HTTPBasicAuth(user_name, user_pwd))

    if response.ok:
        print('Authorized')
        with open('auth.json', 'w') as resp:
            data = {
                'headers': dict(response.headers),
                'response': json.loads(response.text)
            }
            print('auth.json created')
            resp.write(json.dumps(data, indent=4))
    else:
        print('Wrong user name or password')