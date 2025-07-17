#!/usr/bin/env python3

from copy import copy
from pprint import pprint
from time import sleep
import csv
import itertools
import sys
import webbrowser

from click.testing import CliRunner
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import click
import pytest

# import browser_cookie3
# import requests
# from diskcache import Cache

# Initialize the Flow using client_secret.json downloaded from the Cloud Console
flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    ['https://www.googleapis.com/auth/photoslibrary.readonly']
)

# Run the flow to get credentials
credentials = flow.run_local_server(port=0)

# Save the credentials
with open('token.json', 'w') as f:
    f.write(credentials.to_json())

# Load the credentials
creds = None
if creds and not creds.valid:
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

# Build the Google Photos API client
service = build('photoslibrary', 'v1', credentials=creds)

# Make a request to the API
results = service.albums().list(
    pageSize=10, fields="nextPageToken,albums(id,title)"
).execute()

# Do something with the results
albums = results.get('albums', [])
for album in albums:
    print(album['title'])

@click.group()
def control():
    pass


@control.command("test")
def check():
    pytest.main([__file__])


def get_pairs(players):
    return (sorted(match) for match in itertools.combinations(players, 2))


def get_fixtures(players):
    players = copy(players)
    if len(players) % 2:
        players.append("BYE")
    n = len(players)
    matchs = []
    fixtures = []
    for fixture in range(1, n):
        for i in range(n // 2):
            matchs.append(sorted([players[i], players[n - 1 - i]]))
        players.insert(1, players.pop())
        fixtures.insert(len(fixtures) // 2, matchs)
        matchs = []
    return fixtures


def test__list_pairs__even():
    stdin = "a\nb\nc\nd"
    result = set(_list_pairs(stdin).splitlines())
    answer = set(
        (
            "a vs b",
            "c vs d",
            "a vs c",
            "b vs d",
            "b vs c",
            "a vs d",
        )
    )
    assert answer == result


def test__list_pairs__odd():
    stdin = "a\nb\nc"
    result = set(_list_pairs(stdin).splitlines())
    answer = set(
        (
            "a vs b",
            "BYE vs c",
            "a vs c",
            "BYE vs b",
            "b vs c",
            "BYE vs a",
        )
    )
    assert answer == result


def test__list_fixtures__1():
    stdin = "a"
    result = _list_fixtures(stdin)
    answer = "\n# ROUND 1\nBYE vs a"
    assert answer == result


def test__list_fixtures__2():
    stdin = "a\nb"
    result = _list_fixtures(stdin)
    answer = "\n# ROUND 1\na vs b"
    assert answer == result


def test__list_fixtures__even():
    stdin = "a\nb\nc\nd"
    result = _list_fixtures(stdin)
    result = {
        line.strip() for line in result.splitlines() if line if not line.startswith("#")
    }
    answer = set(_list_pairs(stdin).splitlines())
    assert answer == result


def test__list_fixtures__odd():
    stdin = "a\nb\nc"
    result = _list_fixtures(stdin)
    result = {
        line.strip() for line in result.splitlines() if line if not line.startswith("#")
    }
    answer = set(_list_pairs(stdin).splitlines())
    assert answer == result


@control.command()
@click.argument("players_file", type=click.File("r"), default=sys.stdin)
def list_pairs(players_file):
    with players_file:
        data = players_file.read()
    print(_list_pairs(data))


@control.command()
@click.argument("players_file", type=click.File("r"), default=sys.stdin)
def list_fixtures(players_file):
    with players_file:
        data = players_file.read()
    print(_list_fixtures(data))


def _list_fixtures(data):
    players = [row.strip() for row in data.splitlines() if row]
    fixtures = get_fixtures(players)
    output = []
    for fixture_no, fixture in enumerate(fixtures, 1):
        output.append(f"\n# ROUND {fixture_no}")
        for match in fixture:
            output.append(f"{match[0]} vs {match[1]}")
    return "\n".join(output)


def _list_pairs(data):
    players = [row.strip() for row in data.splitlines() if row]
    if len(players) % 2:
        players.append("BYE")
    output = []
    for left, right in get_pairs(players):
        output.append(f"{left} vs {right}")
    return "\n".join(output)


@control.command()
def ipython():
    import IPython
    IPython.embed()


if __name__ == "__main__":
    control()
