DROP TABLE IF EXISTS Completes;

CREATE TABLE Player (
  steamid CHAR(20) PRIMARY KEY,
  playerName CHAR(50),
  profileurl TEXT,
  avatar TEXT
);

CREATE TABLE Friends (
  player1id CHAR(20),
  player2id CHAR(20),
  PRIMARY KEY (player1id,player2id)
);

CREATE TABLE Groups (
  groupid CHAR(20) PRIMARY KEY,
  groupName CHAR(50),
  headline TEXT,
  summary TEXT,
  avatar TEXT
);

CREATE TABLE MemberOf (
  steamid CHAR(20),
  groupid CHAR(20),
  PRIMARY KEY (steamid, groupid)
);

CREATE TABLE Game (
  appid INT PRIMARY KEY,
  gameName CHAR(50),
  gameVersion TEXT
);

CREATE TABLE Plays (
  steamid CHAR(20),
  appid INT,
  playtime INT,
  PRIMARY KEY (steamid, appid)
);

CREATE TABLE Achievement (
  appid INT,
  achievementName CHAR(100),
  globalCompletePercentage REAL,
  PRIMARY KEY (appid, achievementName)
);

CREATE TABLE Completes (
  steamid CHAR(20),
  appid INT,
  achievementName CHAR(100),
  PRIMARY KEY (steamid, appid, achievementName)
);

CREATE TABLE News (
  gid CHAR(25) PRIMARY KEY,
  appid INT,
  title TEXT,
  author TEXT,
  url TEXT
);

