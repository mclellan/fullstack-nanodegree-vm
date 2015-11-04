-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.
CREATE DATABASE tournament;

DROP VIEW IF EXISTS standings;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;

CREATE TABLE players (
id serial PRIMARY KEY,
name varchar
);

CREATE TABLE matches (
id serial PRIMARY KEY,
player_one_id serial references players(id),
player_two_id serial references players(id),
player_one_game_wins integer,
player_two_game_wins integer,
draws integer
);

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
FROM players p
JOIN matches m on m.player_one_id = p.id or m.player_two_id = p.id
GROUP BY p.id, p.name
ORDER BY match_points DESC
;

