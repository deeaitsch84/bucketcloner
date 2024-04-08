import os
from typing import Union, Optional

import git
import requests


def add_credentials(url: str, user: str, password: str) -> Union[str, None]:
    """Adding username and password to the URL.
    URL may contain the username in the form of http(s)://user@example.com
    or just the url http(s)://example.com and will return
    https://user:password@example.com

    Args:
        url (str): source url
        user (str): username
        password (str): password

    Returns:
        str: url with credentials, None if invalid url
    """
    if '@' in url:
        repo = url.split('@')[1]
    elif '//' in url:
        repo = url.split('//')[1]
    else:
        print(f'Invalid URL: {url}')
        return None
    url = 'https://' + user + ':' + password + '@' + repo
    return url


def clone_workspace(user: str, password: str, workspace: str, repositories: list[str]) -> None:
    """
    Cloning all repositories

    Args:
        user (str): username
        password (str): password
        workspace (str): workspace name
        repositories (list[str] | None): repository names
    """

    url = f'https://api.bitbucket.org/2.0/repositories/{workspace}?pagelen=10'

    while (resp := requests.get(url, auth=(user, password))).status_code == 200:
        jresp = resp.json()

        for repo in jresp['values']:
            if repo['scm'] == 'git':

                # Checking if there is a https clone link
                repo_url = None
                for clone in repo['links']['clone']:
                    if clone['name'] == 'https':
                        repo_url = clone['href']
                        break

                if repo_url is None:
                    print(f'Skipping {repo["name"]} because there is no https clone link.')
                    continue

                already_exists = os.path.exists(f'{workspace}/{repo["name"]}')
                skip = repositories and repo["name"] not in repositories

                if skip:
                    print(f'Skipping {workspace}/{repo["name"]} because it is not in the list of repositories.')
                elif already_exists:
                    print(f'Fetching {workspace}/{repo["name"]} because it already exists.')
                    repo = git.Repo(f'{workspace}/{repo["name"]}')
                    repo.remotes.origin.fetch()
                else:
                    print(f'Cloning {workspace}/{repo["name"]} because it does not exist.')
                    repo_url = add_credentials(repo_url, user, password)
                    git.Repo.clone_from(repo_url, f'{workspace}/{repo["name"]}')

            else:
                print(f'Skipping {repo["name"]} because it is not a git but a {repo["scm"]} repository.')

        if 'next' not in resp.json():
            break
        url = resp.json()['next']
    else:
        print(f'The url {url} returned status code {resp.status_code}.')


def clone_bitbucket(user: str, password: str, workspaces: Union[str, None], repositories: list[str]) -> None:
    """
    Cloning all repositories

    Args:
        user (str): username
        password (str): password
        workspaces (str | None): workspace name
        repositories (str | None): repository name
    """

    print(f'Fetching workspaces {user} {password}')

    if workspaces is None:
        workspaces = [w['slug'] for w in list_workspaces(user, password)]
    else:
        workspaces = workspaces.split(',')

    for workspace in workspaces:
        if not os.path.exists(workspace):
            os.mkdir(workspace)
        clone_workspace(user, password, workspace, repositories)


def list_workspaces(user: str, password: str) -> list:
    """
    List all workspaces

    Args:
        user (str): username
        password (str): password

    Returns:
        list: List of workspaces (dict with name, slug, and url as entries)
    """
    url = "https://api.bitbucket.org/2.0/workspaces"

    workspaces = []

    while (resp := requests.get(url, auth=(user, password))).status_code == 200:
        jresp = resp.json()

        for workspace in jresp['values']:
            w = {
                'name': workspace['name'],
                'slug': workspace['slug'],
                'url': workspace['links']['html']['href']
            }
            workspaces.append(w)

        if 'next' not in resp.json():
            break
        url = resp.json()['next']

    else:
        print(f'The url {url} returned status code {resp.status_code}.')

    return workspaces
