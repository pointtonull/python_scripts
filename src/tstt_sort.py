#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
# "trueskillthroughtime",
# ]
# ///

import os
import pickle
from pathlib import Path
from math import ceil, log
from itertools import combinations

from trueskillthroughtime import factorgraph as fg
from trueskillthroughtime.inference import run

HOME = Path.home()
LEAGUE_PATH = HOME / ".elo_sort/tstt_leagues"
LEAGUE_PATH.mkdir(parents=True, exist_ok=True)

DEFAULT_MU = 25.0
DEFAULT_SIGMA = 8.333
DECAY_RATE = 0.05  # Soft pull toward prior


class TSTTLeague:
    def __init__(self):
        self.matches = []  # list of (winner, loser)
        self.players = set()
        self.skill = {}  # player -> (mu, sigma)

    @classmethod
    def load(cls, name):
        path = LEAGUE_PATH / name
        if path.exists():
            with open(path, "rb") as f:
                return pickle.load(f)
        else:
            league = cls()
            league._path = path
            return league

    def save(self):
        with open(self._path, "wb") as f:
            pickle.dump(self, f)

    def add_players(self, players):
        for p in players:
            if p not in self.skill:
                self.skill[p] = (DEFAULT_MU, DEFAULT_SIGMA)
            self.players.add(p)

    def add_result(self, winner, loser):
        self.matches.append((winner, loser))

    def _apply_decay(self):
        for player in self.players:
            mu, sigma = self.skill[player]
            mu += (DEFAULT_MU - mu) * DECAY_RATE
            sigma += (DEFAULT_SIGMA - sigma) * DECAY_RATE
            self.skill[player] = (mu, sigma)

    def _build_factor_graph(self):
        g = fg.FactorGraph()
        skill_vars = {p: g.add_variable(f"skill_{p}", DEFAULT_MU, DEFAULT_SIGMA) for p in self.players}
        for winner, loser in self.matches:
            fg.add_match(g, skill_vars[winner], skill_vars[loser])
        return g, skill_vars

    def get_ranked_players(self):
        g, skill_vars = self._build_factor_graph()
        run(g)
        posteriors = [(skill_vars[p].value[0], p) for p in self.players]
        posteriors.sort(reverse=True)
        return [p for _, p in posteriors]

    def recommend_pair(self):
        # Simplified: pick pair with closest mu values
        best_pair = None
        best_gap = float("inf")
        for a, b in combinations(self.players, 2):
            mu_a, _ = self.skill[a]
            mu_b, _ = self.skill[b]
            gap = abs(mu_a - mu_b)
            if gap < best_gap:
                best_gap = gap
                best_pair = (a, b)
        return best_pair


def sorted_tstt(players, league_name, top=None, limit=None, key=None, minimum=0):
    players = set(players)
    top = len(players) if top is None else top
    if limit is None:
        limit = ceil(len(players) * log(len(players)))
    limit = max(limit, minimum)

    league = TSTTLeague.load(league_name)
    league.add_players(players)

    for _ in range(limit):
        league._apply_decay()
        try:
            a, b = league.recommend_pair()
        except Exception:
            break

        ka = key(a) if key else a
        kb = key(b) if key else b

        if ka < kb:
            league.add_result(b, a)
        else:
            league.add_result(a, b)

    league.save()
    return league.get_ranked_players()
