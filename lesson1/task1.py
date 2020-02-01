import json
import requests

if __name__ == '__main__':
    user_name = input('Insert github user name: ')

    url = 'https://api.github.com'
    request = f'/users/{user_name}/repos'

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Accept': 'application/vnd.github.v3+json'
    }

    response = requests.get(url+request, headers=headers)
    repos_data = json.loads(response.text)

    if repos_data:
        file_name = '{user_name}_repos.json'
        with open(file_name, 'w') as repos:
            repos.write(json.dumps(repos_data, indent=4))
        print(f'Data saved to {file_name}')

        print('Repositories:')
        for repo in repos_data:
            print(repo['name'])
    else:
        print('There are no repositories')