#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "trueskillthroughtime",
# ]
# ///

from math import ceil, log
from itertools import combinations

from trueskillthroughtime import History, Gaussian


DEFAULT_MU = 25.0
DEFAULT_SIGMA = 8.333
DECAY_RATE = 0.05  # Soft pull toward prior


class TSTTLeague:
    def __init__(self):
        self.matches: list[tuple[str, str]] = []  # list of (winner, loser)
        self.players: set[str] = set()
        self.skill: dict[str, tuple[float, float]] = {}  # player -> (mu, sigma)

    def add_players(self, players):
        for player in players:
            if player not in self.skill:
                self.skill[player] = (DEFAULT_MU, DEFAULT_SIGMA)
            self.players.add(player)

    def add_result(self, winner, loser):
        self.matches.append((winner, loser))

    def _apply_decay(self):
        for player in self.players:
            mu, sigma = self.skill[player]
            mu += (DEFAULT_MU - mu) * DECAY_RATE
            sigma += (DEFAULT_SIGMA - sigma) * DECAY_RATE
            self.skill[player] = (mu, sigma)

    def _build_model(self):
        # If no comparisons, use default mu
        if not self.matches:
            return {p: DEFAULT_MU for p in self.players}

        # Build composition and results for History
        # composition: list of events, each event is [team_winner, team_loser]
        composition = []
        results = []
        for winner, loser in self.matches:
            composition.append([[winner], [loser]])
            results.append([1, 0])

        hist = History(composition, results)
        curves = hist.learning_curves()

        means = {}
        for p in self.players:
            if p in curves and curves[p]:
                # curves[p] is list of (time, Gaussian)
                _, gauss = curves[p][-1]
                means[p] = gauss.mu
            else:
                means[p] = DEFAULT_MU
        return means

    def get_ranked_players(self):
        means = self._build_model()
        # Sort descending by mean
        return [p for p in sorted(means, key=lambda x: -means[x])]

    def recommend_pair(self) -> tuple[str, str]:
        # Pick pair with closest current mu (from self.skill)
        best_pair = None
        best_gap = float("inf")
        for a, b in combinations(self.players, 2):
            mu_a, _ = self.skill[a]
            mu_b, _ = self.skill[b]
            gap = abs(mu_a - mu_b)
            if gap < best_gap:
                best_gap = gap
                best_pair = (a, b)
        if best_pair is None:
            raise RuntimeError("league perfectly sorted")
        return best_pair


# In-memory leagues for testing and scripting
LEAGUE_CACHE = {}


def sorted_tstt(players, league_name=None, top=None, limit=None, key=None, minimum=0):
    """
    Sort players by TrueSkill Through time.

    Parameters
    ----------
    players : list of str
        List of players to sort.
    league_name : str, optional
        Name of the league to use. If not found, a new league is created. If None, the league is not saved.
    top : int, optional
        Number of players to consider for the recommendation. If None, all players are considered.
    limit : int, optional
        Maximum number of iterations to run. If None, the limit is set to N*log(N)
    key : callable, optional
        Function to use to sort the players.
    minimum : int, optional
        Minimum number of iterations to run. If None, the minimum is set to 0.
    """
    if len(players) < 2:
        return players
    players = set(players)
    if limit is None:
        limit = ceil(len(players) * log(len(players)))
    limit = max(limit, minimum)

    if league_name is None:
        league = TSTTLeague()
    else:
        league = LEAGUE_CACHE.get(league_name)
        if league is None:
            league = TSTTLeague()
            LEAGUE_CACHE[league_name] = league

    league.add_players(players)

    for _ in range(limit):
        try:
            left, right = league.recommend_pair()
        except Exception:
            break
        key_left = key(left) if key else left
        key_right = key(right) if key else right
        if key_left < key_right:
            league.add_result(right, left)
        else:
            league.add_result(left, right)

    return league.get_ranked_players()
