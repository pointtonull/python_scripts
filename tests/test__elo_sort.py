from pytest import approx

from src import elo_sort


"""
>>> from statistics import NormalDist
>>> NormalDist(mu=2.5, sigma=1).overlap(NormalDist(mu=5.0, sigma=1))
0.2112995473337106
"""


def test__simple_match():
    league = elo_sort.League()
    league.add_players(["Adrian", "Beatriz"])

    assert len(league.elos) == 2
    assert league.k("Adrian") > 0
    assert league.k("Beatriz") > 0

    league.add_result("Adrian", ">", "Beatriz")

    assert league.games["Adrian"] == 1
    assert league.games["Beatriz"] == 1
    assert league.elos["Adrian"] > league.elos["Beatriz"]


def test__get_expected_result():
    expected_result = elo_sort.get_expected_result(1500, 1500)
    assert expected_result == 0.5

    expected_result = elo_sort.get_expected_result(1800, 1500)
    assert expected_result > 0.5

    expected_result = elo_sort.get_expected_result(1500, 1800)
    assert expected_result < 0.5


def test__k_stabilizes():
    league = elo_sort.League()
    league.add_players(["Adrian", "Beatriz"])

    elos_Adrian = []
    elos_Beatriz = []
    elos_Adrian.append(league.elos["Adrian"])
    elos_Beatriz.append(league.elos["Beatriz"])
    league.add_result("Adrian", ">", "Beatriz")
    elos_Adrian.append(league.elos["Adrian"])
    elos_Beatriz.append(league.elos["Beatriz"])
    league.add_result("Adrian", ">", "Beatriz")
    elos_Adrian.append(league.elos["Adrian"])
    elos_Beatriz.append(league.elos["Beatriz"])
    league.add_result("Adrian", ">", "Beatriz")
    elos_Adrian.append(league.elos["Adrian"])
    elos_Beatriz.append(league.elos["Beatriz"])
    league.add_result("Adrian", ">", "Beatriz")
    elos_Adrian.append(league.elos["Adrian"])
    elos_Beatriz.append(league.elos["Beatriz"])

    assert elos_Adrian == sorted(elos_Adrian)
    assert elos_Adrian == approx([1500, 1700, 1751, 1784, 1801], abs=0.5)
    diffs_Adrian = [b - a for a, b in zip(elos_Adrian[:-1], elos_Adrian[1:])]
    assert diffs_Adrian == sorted(diffs_Adrian, reverse=True)
    assert diffs_Adrian == approx([200, 51, 33, 16], abs=0.5)

    assert elos_Beatriz == sorted(elos_Beatriz, reverse=True)
    assert elos_Beatriz == approx([1500, 1300, 1249, 1216, 1199], abs=0.5)
    diffs_Beatriz = [b - a for a, b in zip(elos_Beatriz[:-1], elos_Beatriz[1:])]
    assert diffs_Beatriz == sorted(diffs_Beatriz)
    assert diffs_Beatriz == approx([-200, -51, -33, -16], abs=0.5)


def _test__recommends_matches():
    league = elo_sort.League()
    players = set(["Adrian", "Beatriz", "Carlos", "Daniel", "Ellie", "Fabio"])
    league.add_players(["Adrian", "Beatriz", "Carlos", "Daniel", "Ellie", "Fabio"])

    # adds matches for everybody but Carlos and Daniel
    league.add_result("Adrian", ">", "Fabio")
    league.add_result("Beatriz", ">", "Ellie")

    # now the recommended matches should start with Carlos - Daniel
    # because they are still undefeated
    recommended_match = league.recommended_match()[0]
    assert set(recommended_match) == set(("Carlos", "Daniel"))

    league.add_result("Carlos", ">", "Daniel")

    recommended_match = league.recommended_match(
        players=["Adrian", "Beatriz", "Daniel", "Fabio"]
    )[0]
    assert set(recommended_match) == set(("Adrian", "Beatriz"))

    league.add_result("Adrian", ">", "Beatriz")
    recommended_match = league.recommended_match(players=players - {"Daniel"})[0]
    assert "Carlos" in recommended_match

    league.add_result("Beatriz", ">", "Carlos")
    recommended_match = league.recommended_match(top=3)[0]
    assert "Carlos" in recommended_match

    # it should always have a recommended match
    for i in range(10):
        recommended_match = league.recommended_match()[0]
        assert recommended_match is not None
        white, black = recommended_match
        league.add_result(white, ">", black)
