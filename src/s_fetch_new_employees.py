#!/usr/bin/env python3

from datetime import date, timedelta
from time import sleep
import csv
import sys
import webbrowser

from diskcache import Cache
import browser_cookie3
import requests
import click
import pytest


DOMAIN = "spireglobal.bamboohr.com"
BASE_URL = f"https://{DOMAIN}"
LOGIN_URL = f"{BASE_URL}/login"
SESSION = None
CACHE = Cache("~/.bamboohr_cache")
DAY = timedelta(1)

def deep_get(dictionary, key):
    try:
        result = dictionary.get(key)
    except AttributeError:
        return None
    if result is None:
        for value in dictionary.values():
            result = deep_get(value, key)
            if result is not None:
                return result
    else:
        return result

def pprint(object, indent=0):
    if type(object) is dict:
        if set(object) == {"id", "question", "answer"}:
            if object["answer"]:
                print(f"{' '*indent}- {object['question']}")
                print(f"{' '*indent}  {object['answer']}")
        elif name := object.pop("preferredFullName", None):
            complete_name = (", ".join(object.pop(k) for k in sorted(k for k in object.keys() if k .endswith("Name"))))
            print(f"{' '*indent}{name} ({complete_name}):")
            pprint(object, indent+2)
        else:
            for key in object:
                if key == "id":
                    continue
                print(f"{' '*indent}{key}:")
                pprint(object[key], indent+2)
    elif type(object) is list:
        for item in object:
            pprint(item, indent+2)
    elif type(object) is str:
        print(f"{' '*indent}{object}")
    else:
        print(f"{' '*indent}{type(object)} {object}")

class CookieManager:
    cookies = None

    def __init__(self, domain: str):
        self.domain = domain

    def read_cookie(self, cookie_name, force_refresh=False):
        if force_refresh or self.cookies is None:
            self.cookies = browser_cookie3.firefox(domain_name=self.domain)
        try:
            cookie = deep_get(self.cookies._cookies, cookie_name)
        except KeyError:
            cookie = None
        return cookie

    def get_token(self):
        access_token = self.read_cookie("PHPSESSID")

        if access_token:
            return access_token

        print("please log-in")
        print(self.cookies)
        webbrowser.get("firefox").open(LOGIN_URL)
        for attempt in range(20):
            sleep(1)
            access_token = self.read_cookie("access_token", force_refresh=True)
            if access_token:
                return access_token
        else:
            print("could not get access_token in allotted attempts")
            return

    def _parse_ids(self, result):
        content_key = next(iter(result.keys()))
        content = result[content_key]
        item = next(iter(content))
        id_key = next(key for key in item.keys() if key.endswith("Id") if key.startswith(content_key))
        return [item[id_key] for item in content]


class BAMBOOHR:
    session = requests.Session()
    cookie_manager = CookieManager(DOMAIN)

    def __init__(self):
        access_token = self.cookie_manager.get_token()
        if not access_token:
            raise RuntimeError("not session available")
        self.session.cookies.update(self.cookie_manager.cookies)

    def paginate(self, method, url, *args, **kwargs):
        params = kwargs.get("params", {})
        kwargs["params"] = params
        seen_ids = set()

        while True:
            result = method(url, *args, **kwargs)

            if isinstance(result, list):
                content = result
                ids = result
            elif isinstance(result, dict):
                content = self._parse_content(result)
                ids = self._parse_ids(result)
            else:
                raise NotImplementedError(f"Unknown {type(result)=}")

            last_id = ids[-1]
            new_ids = set(ids) - seen_ids
            if "rows" in params and len(content) < int(params["rows"]):
                break
            if not new_ids:
                break
            seen_ids |= new_ids
            yield from content
            params["startKey"] = last_id

    @CACHE.memoize(ignore=[0])
    def get(self, url, *args, **kwargs):
        url = f"{BASE_URL}/{url}"
        headers = kwargs.get("headers", {})
        headers["User-Agent"] = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) "
            "Gecko/20100101 Firefox/111.0")
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        kwargs["headers"] = headers
        response = self.session.get(url, *args, **kwargs)
        response.raise_for_status()
        return response.json()



def initialize():
    global SESSION
    if SESSION is None:
        SESSION = BAMBOOHR()


@click.group()
def control():
    initialize()


def _is_iterable(instance):
    try:
        iterator = iter(instance)
        return True
    except TypeError:
        return False


@control.command("test")
def check():
    pytest.main([__file__])


def test__get_hired__today():
    initialize()
    employees = get_hired(date.today())
    assert _is_iterable(employees)


def get_hired(day):
    url = f"onboarding/api/gtky/{day.isoformat()}"
    data = SESSION.get(url)
    employees = data["employeeData"]
    for employee in employees:
        employee["hired"] = day.isoformat()
        yield employee


@control.command()
@click.argument("day", nargs=1)
def list_hired(day):
    day = date.fromisoformat(day)
    for employee in get_hired(day):
        pprint(employee)


@control.command()
@click.argument("day", nargs=1)
def list_hired_since(day):
    day = date.fromisoformat(day)
    while day <= date.today():
        for employee in get_hired(day):
            print("--")
            pprint(employee)
        day += DAY



@control.command()
def ipython():
    import IPython
    IPython.embed()


if __name__ == "__main__":
    control()
