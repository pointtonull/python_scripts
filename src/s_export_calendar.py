#!/usr/bin/env python3

import json
import re
import math
import webbrowser
from time import sleep

from bs4 import BeautifulSoup
from diskcache import Cache
from progressbar import bar
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import browser_cookie3
import click
import pytest


DOMAIN = "outlook.office365.us"
URL_CALENDAR = f"https://{DOMAIN}/calendar/view/day"
URL_LOGIN = f"https://{DOMAIN}/calendar/view/day"
SESSION = None
CACHE = Cache("~/.calendar_cache")


class FirefoxDriver(webdriver.Firefox):

    retry_attemps: int = 2
    default_kwargs = {
    }

    def __init__(self, **kwargs):
        geckodriver_path = "/usr/local/bin/geckodriver"

        options = Options()
        options.add_argument("-headless")
        self.default_kwargs.update(kwargs)
        kwargs["options"] = options
        super().__init__(options=options, **self.default_kwargs)

class CookieManager:
    cookies = None

    def __init__(self, domain: str):
        self.domain = domain
        self.cookies = [cookie.__dict__ for cookie in browser_cookie3.firefox(domain_name=self.domain)]

class OUTLOOK:
    driver: FirefoxDriver
    initialized = False

    def __getstate__(self):
        return "stateless"

    def __setstate__(self, state):
        pass

    def __initialize__(self):
        if not self.initialized:
            self.driver = FirefoxDriver()
            self.driver.get(URL_LOGIN)
            self.cookie_manager = CookieManager(DOMAIN)
            for cookie in self.cookie_manager.cookies:
                self.driver.add_cookie(cookie)

    def fetch(self, url, params=None):
        if params is not None:
             url_parts = list(parse.urlparse(url))
             url_params = parse.parse_qs(url_parts[4])
             url_params.update(params)
             url_parts[4] = parse.urlencode(url_params)
             url = parse.urlunparse(url_parts)

        return self._fetch(url)

    @CACHE.memoize(expire=60*60*1, ignore=[0])
    def _fetch(self, url):
        self.__initialize__()
        self.driver.get(url)
        return str(self.driver.page_source)

def initialize():
    global SESSION
    if SESSION is None:
        SESSION = OUTLOOK()


@click.group()
def control():
    initialize()


def _get_today_calendar():
    result = dir(SESSION)
    result = SESSION.fetch(URL_CALENDAR)
    return result


@control.command()
def get_today_calendar():
    result = _get_today_calendar()
    print(result)


@control.command()
def ipython():
    import IPython
    IPython.embed()


if __name__ == "__main__":
    control()
