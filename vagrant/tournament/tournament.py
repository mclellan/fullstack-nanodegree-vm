#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    conn = connect()
    cur = conn.cursor()
    cur.execute('DELETE FROM matches')
    conn.commit()
    conn.close()


def deletePlayers():
    """Remove all the player records from the database."""
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM players")
    conn.commit()
    conn.close()

    
def countPlayers():
    """Returns the number of players currently registered."""
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(ID) FROM players")
    (player_count,) = cur.fetchone()
    conn.close()
    return player_count

    
def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO players (name) values (%s)",(name,))
    conn.commit()
    conn.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        points: the number of match points the player has
         -- wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM standings")
    standings = cur.fetchall()
    conn.close()
    return standings


def reportMatch(player_one_id, player_two_id, player_one_game_wins, player_two_game_wins, draws ):
    """Records the outcome of a single match between two players.
    Args:
      player_one_id:  the id of player one
      player_two_id:  the id of player two
      player_one_game_wins: the number of games player one won
      player_two_game_wins: the number of games player two won
      draws: the number of drawn games
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO matches (player_one_id, player_two_id, player_one_game_wins, player_two_game_wins, draws) values (%s,%s,%s,%s,%s)",(player_one_id, player_two_id, player_one_game_wins, player_two_game_wins, draws))
    conn.commit()
    conn.close()
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pairings")
    pairings = cur.fetchall()
    conn.close()
    return pairings


