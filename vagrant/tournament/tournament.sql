-- Table definitions for the tournament project.
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament

-- Players identified by unique serial id, name can be any string
CREATE TABLE players (
id serial PRIMARY KEY,
name varchar
);

-- matches are recorded with winner and loser 
-- if match_draw flag is set to true win/loss will be ignored
CREATE TABLE matches (
id serial PRIMARY KEY,
winner_id int references players(id),
loser_id int references players(id),
match_draw boolean
);

-- calculates opponent_match_win: count all matches won by opponents
-- for each player in the tournament
CREATE VIEW opponent_match_wins AS
SELECT
p.id
,(SELECT
	COUNT(m.winner_id)
	FROM
	(
		-- select all opponent_ids of p.id
		SELECT 
		CASE WHEN m.winner_id = p.id then m.loser_id else m.winner_id END AS opponent_id
		FROM matches m
		WHERE (m.winner_id = p.id or m.loser_id = p.id)
	) AS o
	JOIN matches m on m.winner_id = o.opponent_id and match_draw = false
) as opponent_match_wins
FROM players p
;

-- standings are extrapolated from players joined to match data
-- 3 points are given for a match win (match_draw = false)
-- 1 points are given for a match tie (match_draw = true)
-- 0 points are given for a match loss (loser_id)
-- points desc determine standings, ties broken by opponent_match_wins desc
CREATE VIEW standings AS 
SELECT
a.id
,a.name
,a.match_points
,a.matches
FROM (
	SELECT 
	p.id
	,p.name
	,(select count(id) from matches where winner_id = p.id and match_draw = false) * 3 + 
	(select count(id) from matches where (winner_id = p.id or loser_id = p.id) and match_draw = true)  	
		AS match_points
	,(select count(id) from matches where (winner_id = p.id) or (loser_id = p.id)) as matches
	,(select opponent_match_wins from opponent_match_wins where id = p.id) 
	FROM players p
	LEFT JOIN matches m on m.winner_id = p.id or m.loser_id = p.id
	GROUP BY p.id, p.name
	ORDER BY match_points DESC, opponent_match_wins DESC
) AS a
;

-- checks bye eligibility by ensuring players with byes are not 
-- at the bottom of standings by giving them a pairings point rating
-- one above the lowest player without a bye-win
-- the lowest player in standings without a bye receives the bye
CREATE VIEW standings_bye_check AS
SELECT
s.id
,s.name
,CASE WHEN m.winner_id IS NOT NULL THEN (
			SELECT 
			MIN(s.match_points) 
			FROM standings s 
			LEFT JOIN (
				SELECT m.winner_id 
				FROM matches m 
				WHERE m.loser_id IS NULL -- get only ids with bye wins
				) AS b ON b.winner_id = s.id
			WHERE b.winner_id IS NULL -- exclude ids with byes
			) + 1 ELSE s.match_points END
,s.matches
FROM standings s
LEFT JOIN matches m on m.winner_id = s.id and m.loser_id IS NULL
;

-- Pairings are created by taking the odd rows from standings_bye_check
-- and joining the even rows directly below
-- if there are an odd number of players the final player recieves a bye
-- pairings are made top down by match_points with exception for byes
CREATE VIEW pairings AS
SELECT 
s.id as player_one_id
,s.name as player_one_name
,s2.id AS player_two_id
,CASE WHEN s2.name IS NULL THEN 'BYE' ELSE s2.name END AS player_two_name
FROM (
	SELECT 
	ROW_NUMBER() OVER(ORDER BY match_points DESC) AS rn
	, *
	FROM standings_bye_check
) AS s
LEFT JOIN (
	SELECT * FROM (
		SELECT 
		ROW_NUMBER() OVER(ORDER BY match_points DESC) AS rn
		, *
		FROM standings_bye_check
	) as even_rows
	WHERE rn % 2 = 0
) AS s2 ON s2.rn - 1 = s.rn
WHERE s.rn % 2 <> 0