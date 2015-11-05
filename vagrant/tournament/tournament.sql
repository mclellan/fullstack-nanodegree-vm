-- Table definitions for the tournament project.
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament

-- Players identified by unique serial id, name can be any string
CREATE TABLE players (
id serial PRIMARY KEY,
name varchar
);

-- matches are recorded with player's ids, individual game wins, and draw count
-- both game win count and draw count are necessary to determine a match winner
CREATE TABLE matches (
id serial PRIMARY KEY,
player_one_id serial references players(id),
player_two_id serial references players(id),
player_one_game_wins integer,
player_two_game_wins integer,
draws integer
);

-- standings are extrapolated from players joined to match data
-- 3 points are given for a match win defined as player game wins > player 2 game wins
-- 1 points are given for a match tie defined as player win # = player 2 win #
-- 0 points are given for a match loss defined as player game win # < player 2 game win #
-- points determine standings desc
CREATE VIEW standings AS 
SELECT 
p.id
,p.name
,(select count(id) from matches where 
	(player_one_id = p.id and player_one_game_wins > player_two_game_wins) or 
	(player_two_id = p.id and player_two_game_wins > player_one_game_wins)) * 3 + 
(select count(id) from matches where 
	(player_one_id = p.id and player_one_game_wins = player_two_game_wins) or 
	(player_two_id = p.id and player_two_game_wins = player_one_game_wins))  	
	AS match_points
,(select count(id) from matches where (player_one_id = p.id) or (player_two_id = p.id)) as matches
FROM players p
LEFT JOIN matches m on m.player_one_id = p.id or m.player_two_id = p.id
GROUP BY p.id, p.name
ORDER BY match_points DESC
;

-- Pairings are created by taking the odd rows from standings
-- and joining the even rows directly below
-- if there are an odd number of players the final player recieves a bye
-- pairings are made top down by match_points
CREATE VIEW pairings AS
SELECT 
s.id as player_one_id
,s.name as player_one_name
,s2.id as player_two_id
,s2.name as player_two_name
FROM (
	SELECT 
	ROW_NUMBER() OVER(ORDER BY match_points DESC) AS rn
	, *
	FROM standings
) AS s
LEFT JOIN (
	SELECT * FROM (
		SELECT 
		ROW_NUMBER() OVER(ORDER BY match_points DESC) AS rn
		, *
		FROM standings
	) as even_rows
	WHERE rn % 2 = 0
) AS s2 ON s2.rn - 1 = s.rn
WHERE s.rn % 2 <> 0