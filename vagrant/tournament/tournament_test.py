#!/usr/bin/env python
#
# Test cases for tournament.py

from tournament import *

def testDeleteMatches():
    deleteMatches()
    print "1. Old matches can be deleted."


def testDelete():
    deleteMatches()
    deletePlayers()
    print "2. Player records can be deleted."


def testCount():
    deleteMatches()
    deletePlayers()
    c = countPlayers()
    if c == '0':
        raise TypeError(
            "countPlayers() should return numeric zero, not string '0'.")
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print "3. After deleting, countPlayers() returns zero."


def testRegister():
    deleteMatches()
    deletePlayers()
    registerPlayer("Chandra Nalaar")
    c = countPlayers()
    if c != 1:
        raise ValueError(
            "After one player registers, countPlayers() should be 1.")
    print "4. After registering a player, countPlayers() returns 1."


def testRegisterCountDelete():
    deleteMatches()
    deletePlayers()
    registerPlayer("Markov Chaney")
    registerPlayer("Joe Malik")
    registerPlayer("Mao Tsu-hsi")
    registerPlayer("Atlanta Hope")
    c = countPlayers()
    if c != 4:
        raise ValueError(
            "After registering four players, countPlayers should be 4.")
    deletePlayers()
    c = countPlayers()
    if c != 0:
        raise ValueError("After deleting, countPlayers should return zero.")
    print "5. Players can be registered and deleted."


def testStandingsBeforeMatches():
    deleteMatches()
    deletePlayers()
    registerPlayer("Melpomene Murray")
    registerPlayer("Randy Schwartz")
    standings = playerStandings()
    if len(standings) < 2:
        raise ValueError("Players should appear in playerStandings even before "
                         "they have played any matches.")
    elif len(standings) > 2:
        raise ValueError("Only registered players should appear in standings.")
    if len(standings[0]) != 4:
        raise ValueError("Each playerStandings row should have four columns.")
    [(id1, name1, wins1, matches1), (id2, name2, wins2, matches2)] = standings
    if matches1 != 0 or matches2 != 0 or wins1 != 0 or wins2 != 0:
        raise ValueError(
            "Newly registered players should have no matches or wins.")
    if set([name1, name2]) != set(["Melpomene Murray", "Randy Schwartz"]):
        raise ValueError("Registered players' names should appear in standings, "
                         "even if they have no matches played.")
    print "6. Newly registered players appear in the standings with no matches."


def testReportMatches():
    """ modified to account for draws in reportMatch
    modified to account for match_point reporting instead of wins
    """
    deleteMatches()
    deletePlayers()
    registerPlayer("Bruno Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    registerPlayer("Diane Grant")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, False)
    reportMatch(id3, id4, False)
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i in (id1, id3) and w != 3: 
            raise ValueError("Each match winner should have three match points recorded.")
        elif i in (id2, id4) and w != 0:
            raise ValueError("Each match loser should have zero wins recorded.")
    print "7. After a match, players have updated standings."
	
def testPairings():
    """ modified to account for draws in reportMatch """
    deleteMatches()
    deletePlayers()
    registerPlayer("Twilight Sparkle")
    registerPlayer("Fluttershy")
    registerPlayer("Applejack")
    registerPlayer("Pinkie Pie")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, False)
    reportMatch(id3, id4, False)
    pairings = swissPairings()
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = set([frozenset([id1, id3]), frozenset([id2, id4])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, players with one win should be paired.")
    print "8. After one match, players with one win are paired."

def testReportMatchesDraws():
    """ tests if reporting matches as draws works
    """
    deleteMatches()
    deletePlayers()
    registerPlayer("Bruno Walton")
    registerPlayer("Boots O'Neal")
    registerPlayer("Cathy Burton")
    registerPlayer("Diane Grant")
    standings = playerStandings()
    [id1, id2, id3, id4] = [row[0] for row in standings]
    reportMatch(id1, id2, True)
    reportMatch(id3, id4, False)
    standings = playerStandings()
    for (i, n, w, m) in standings:
        if m != 1:
            raise ValueError("Each player should have one match recorded.")
        if i == id3 and w != 3: 
            raise ValueError("Each match winner should have three match points recorded.")
        elif i == id4 and w != 0:
            raise ValueError("Each match loser should have zero match points recorded.")
        elif i in (id1, id2) and w != 1:
            raise ValueError("Each player with a draw should have one match point recorded.")
    print "9. After a match with draws, players have updated standings."

def testBye():
    """ testing bye reporting and matching """
    deleteMatches()
    deletePlayers()
    registerPlayer("Twilight Sparkle")
    registerPlayer("Fluttershy")
    registerPlayer("Applejack")
    standings = playerStandings()
    [id1, id2, id3] = [row[0] for row in standings]
    reportMatch(id1, id2, False)
    reportMatch(id3,None, False)
    pairings = swissPairings()
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = set([frozenset([id1, id3]), frozenset([id2, None])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "After one match, the lowest player should recieve a bye.")
    print "10. Players received a bye when there were not enough players."

def testByeRestriction():
    """ testing no-multiple-bye restriction """
    deleteMatches()
    deletePlayers()
    registerPlayer("Billy")
    registerPlayer("Jake")
    registerPlayer("Tangent")
    standings = playerStandings()
    [id1, id2, id3] = [row[0] for row in standings]
    reportMatch(id1, id2, False)
    reportMatch(id3, None, False)
    reportMatch(id1, id3, False)
    reportMatch(id2, None, False)
    pairings = swissPairings()
    # id1 is the only player without a bye and should recieve one in these pairings
	# despite the fact that id1 would be paired with id2/id3 in normal circumstances
	# given the match_points 
    # id   | match_points | matches 
    #------+--------------+---------
    # id1  |            6 |       2
    # id3  |            3 |       2
    # id2  |            3 |       2
    if len(pairings) != 2:
        raise ValueError(
            "For four players, swissPairings should return two pairs.")
    [(pid1, pname1, pid2, pname2), (pid3, pname3, pid4, pname4)] = pairings
    correct_pairs = set([frozenset([id1, None]), frozenset([id2, id3])])
    actual_pairs = set([frozenset([pid1, pid2]), frozenset([pid3, pid4])])
    if correct_pairs != actual_pairs:
        raise ValueError(
            "id2 or id3 have received a bye which violates one-bye rule")
    print "11. Players were prevented from receiving two byes."

def testOpponentMatchWinStandings():
    """ test that ties are broken by opponent match wins """
    deleteMatches()
    deletePlayers()
    registerPlayer("Dan")
    registerPlayer("Jan")
    registerPlayer("Pan")
    registerPlayer("Fan")
    registerPlayer("Yan")
    registerPlayer("Man")
    standings = playerStandings()
    [id1, id2, id3, id4, id5, id6] = [row[0] for row in standings]
    reportMatch(id1, id2, False) # id1 : 3, id2 : 0
    reportMatch(id3, id4, False) # id3 : 3, id4 : 0
    reportMatch(id5, id6, False) # id5 : 3, id6 : 0
    reportMatch(id1, id3, False) # id1 : 6, id3 : 3
    reportMatch(id5, id2, False) # id5 : 6, id2 : 0
    reportMatch(id4, id6, False) # id4 : 3, id6 : 0
    standings = playerStandings()
    [pid1, pid2, pid3, pid4, pid5, pid6] = [row[0] for row in standings]
    correct_ranks = set(frozenset([id1, id5])) 
    actual_ranks = set(frozenset([pid1, pid2]))
    if correct_ranks != actual_ranks:
        raise ValueError(
            "id1 should be ranked higher than id5 based on more opponent_match_wins")
    print "12. Ties are broken by opponent match wins."

if __name__ == '__main__':
    testDeleteMatches()
    testDelete()
    testCount()
    testRegister()
    testRegisterCountDelete()
    testStandingsBeforeMatches()
    testReportMatches()
    testPairings()
    testReportMatchesDraws()
    testBye()
    testByeRestriction()
    testOpponentMatchWinStandings()
    print "Success!  All tests pass!"


