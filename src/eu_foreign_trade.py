#!/usr/bin/env python

import requests
from diskcache import Cache
from icecream import ic

CACHE = Cache("~/.cache/eu_foreign_trade")

BASE_URL = "https://oec.world/api/olap-proxy/data"

session = requests.session()


@CACHE.memoize(expire=60 * 60 * 24)
def query(params):
    response = session.get(BASE_URL, params=params)
    response.raise_for_status()
    return response


def get_data(cube, drilldown, measures, parents=True, sparce=False):
    parents = str(parents).lower()
    sparce = str(sparce).lower()
    response = query(
        {
            "cube": cube,
            "drilldowns": drilldown,
            "measures": measures,
            "parents": parents,
            "sparse": sparce,
        }
    )
    return response.json()

    """

        "Exporter Country": "euaut",
        "Exporter Country": "eugbr",
        "Year": "2022",
        "cube": "trade_i_baci_a_92",
        "drilldowns": "HS6",
        "drilldowns": "Year,Importer Country",
        "measures": "Trade Value",
        "parents": "true",
        "properties": "Importer Country ISO 3",
        "sparse": "false",

        "cube": "trade_i_baci_a_96",
        "drilldowns": "Year,Importer Country",
        "measures": "Trade Value",
        "parents": "true",
        "Year": "2018,2019,2020,2021,2022",
        "Exporter Country": "euaut",
        "Importer Country": "eubel",
        "properties": "Importer Country ISO 3",

    """


def main():
    data = get_data()
    print(data.keys())


if __name__ == "__main__":
    main()
