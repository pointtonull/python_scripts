#!/usr/bin/env python

from itertools import takewhile, combinations
from math import log, ceil
from pathlib import Path
from statistics import NormalDist
import os
import pickle
import sys

import click

RESULTS = {
    "<": 0,
    "=": 0.5,
    ">": 1,
}
K_SIGMA = 1  # higher sigma, more priority to new players
LEAGUES_FOLDER = os.path.expanduser("~/.elo_sort/leagues/")
os.makedirs(LEAGUES_FOLDER, exist_ok=True)
OVERLAP_THRESHOLD = 0.01



def calculate_elo(elo, result, expected_result, k):
    new_elo = elo + k * (result - expected_result)
    return new_elo


def get_expected_result(elo_white, elo_black):
    exp = (elo_black - elo_white) / 480.0
    return 1 / ((10.0 ** (exp)) + 1)


class League:
    def __init__(self):
        self.elos = dict()
        self.games = dict()
        self.perfect_score_players = set()

    @classmethod
    def load(cls, name, create=False):
        name = name or "default"
        path = Path(LEAGUES_FOLDER) / name
        try:
            with open(path, "rb") as file:
                league = pickle.load(file)
        except FileNotFoundError:
            if not create:
                raise
            league = cls()
        league.path = path
        return league

    def save(self, name=None):
        if name is None:
            if self.path is None:
                raise ValueError("League has no path or name")
            else:
                path = self.path
        else:
            path = Path(LEAGUES_FOLDER) / name
        with open(path, "wb") as file:
            pickle.dump(self, file)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.save()

    def _add_player(self, name, rating=1500, games=0):
        self.elos[name] = rating
        self.games[name] = games
        self.perfect_score_players.add(name)

    def add_players(self, players, on_conflict="ignore"):
        for player in players:
            if player in self.elos:
                if on_conflict == "ignore":
                    continue
                else:
                    raise ValueError(f"Player {player} already exists")
            self._add_player(player)

    def k(self, player):
        return 800 / max(self.games[player], 2)

    def add_result(self, white, relation, black):
        elo_white = self.elos[white]
        elo_black = self.elos[black]
        result = RESULTS[relation]
        expected_result = get_expected_result(elo_white, elo_black)
        if relation in "=>":
            self.perfect_score_players.discard(black)
        if relation in "<=":
            self.perfect_score_players.discard(white)
        new_elo_white = calculate_elo(
            elo=elo_white,
            result=result,
            expected_result=expected_result,
            k=self.k(white),
        )
        new_elo_black = calculate_elo(
            elo=elo_black,
            result=(1 - result),
            expected_result=(1 - expected_result),
            k=self.k(black),
        )
        self.elos[white] = new_elo_white
        self.elos[black] = new_elo_black
        self.games[white] += 1
        self.games[black] += 1

    def _get_norm_dist(self, player):
        sigma = (self.k(player)) ** K_SIGMA
        mu = self.elos[player]
        return NormalDist(mu=mu, sigma=sigma)

    def get_ranking(self, players=None) -> list[tuple[int, str]]:
        if players is None:
            players = self.elos.keys()
        elos_players = [(self.elos[player], player) for player in players]
        elos_players.sort(reverse=True, key=lambda elo_player: elo_player[0])
        return elos_players

    def get_games_played(self, players=None):
        if players is None:
            players = self.games.keys()
        games_players = [(self.games[player], player) for player in players]
        games_players.sort(key=lambda game_player: game_player[0])
        return games_players

    def __repr__(self):
        return "\n".join(f"{player} ({elo})" for elo, player in self.get_ranking())

    def recommended_match(self, players=None, top=None, threshold=OVERLAP_THRESHOLD):
        """
        players with perfect score, that are not the first should be prioritized
        if top is provided, return matches with chances of affecting the top n
        higher k, higher probability
        closer to another player's ELO, higher probability
        """

        # TODO: unbeaten, overlap, fewer matches, clustering
        if players is None:
            players = set(self.elos.keys())
        else:
            players = set(players)

        ranking = self.get_ranking(players)
        top_elo = ranking[0][0]
        top_players = {
            rank[1] for rank in takewhile(lambda rank: rank[0] == top_elo, ranking)
        }

        # unbeaten
        unbeaten_players = (players & self.perfect_score_players) - top_players
        if unbeaten_players:
            ranking = self.get_ranking(unbeaten_players)

        # neglected players
        games_played = self.get_games_played(players)
        fewer_games = games_played[0][0]
        most_games = games_played[-1][0]
        if fewer_games < most_games * 0.50:
            selected = [
                player
                for games, player in games_played
                if games <= most_games * 0.50
            ]
        elif top is None:
            selected = [rank[1] for rank in ranking]
        else:
            selected = set()
            for player in (rank[1] for rank in ranking[:top]):
                norm_dist = self._get_norm_dist(player)
                for other_player in players:
                    if other_player == player:
                        continue
                    other_norm_dist = self._get_norm_dist(other_player)
                    overlap = norm_dist.overlap(other_norm_dist)
                    if overlap > threshold:
                        selected.add(other_player)
            selected = list(selected)

        # overlap
        top_overlap = 0
        top_match = None
        max_lenght = min(len(selected), 3)
        for lenght in range(2, max_lenght + 1):
            for group in (
                selected[f : f + lenght] for f in range(len(selected) - lenght + 1)
            ):
                for left, right in combinations(group, 2):
                    dist_left = self._get_norm_dist(left)
                    dist_right = self._get_norm_dist(right)
                    overlap = dist_left.overlap(dist_right)
                    if overlap > top_overlap:
                        top_overlap = overlap
                        top_match = (left, right)
            if top_overlap > threshold:
                break

        # # closest
        # top_overlap = float("inf")
        # top_match = None
        # for player in selected:
        #     elo_player = self.elos[player]
        #     for elo_opponent, opponent in ranking:
        #         if opponent == player:
        #             continue
        #         diff = abs(elo_player - elo_opponent)
        #         if diff < top_overlap:
        #             top_overlap = diff
        #             top_match = (player, opponent)

        if top_match is None:
            raise RuntimeError("league perfectly sorted")
        return sorted(top_match), top_overlap


def elo_sorted(players, league_name=None, top=None, limit=None, key=None, minimum=0):
    players = set(players)
    top = len(players) if top is None else top
    if limit is None:
        print(f"{len(players)=}")
        limit = ceil(len(players) * log(len(players)))
    limit = max(limit, minimum)
    league = League.load(league_name, create=True)
    league.add_players(players)
    threshold = 0
    for step in range(limit):
        if step >= minimum:
            threshold = OVERLAP_THRESHOLD
        try:
            match, overlap = league.recommended_match(
                top=top, players=players, threshold=threshold
            )
        except RuntimeError:
            break
        white, black = match
        if key is not None:
            k_white = key(white)
            k_black = key(black)
        else:
            k_white = white
            k_black = black
        try:
            if k_white < k_black:
                league.add_result(white, ">", black)
            else:
                league.add_result(white, "<", black)
        except KeyboardInterrupt:
            break
    league.save()
    return [player for _, player in league.get_ranking(players)]


@click.command()
@click.argument("league_name", type=str)
@click.argument("players_file", type=click.File("r"), default=sys.stdin)
@click.option("-t", "--top", type=int)
@click.option("-l", "--limit", type=int)
def main(league_name, top, limit, players_file):
    players = [player.strip() for player in players_file.readlines()]
    print("\n".join(elo_sorted(players, league_name, top, limit)))


if __name__ == "__main__":
    main()
