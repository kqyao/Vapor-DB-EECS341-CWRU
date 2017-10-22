# Vapor-DB-EECS341-CWRU
Course project for EECS3341 Database. A steam info extractor. Working together with Yue (github.com/tripack45)  

Steam® by Valve© is a game platform for vendors to sell game as well as a gamer’s
community. It’s official website claim that “We have thousands of games from Action to Indie
and everything in-between.” and as a game distribution platform they let people “Enjoy exclusive
deals, automatic game updates and other great perks”. As a game community, players will be
able to “meet new people, join game groups, form clans, chat in-game and more” in this
platform.  

Each Steam user has his/her own game “library”, which is a collection of games they owned.
For each game the system keeps track of the player’s playing statistics. These includes playing
time, in-game achievement status and more. A player could “friend” other players, this allows
them to cooperate with or play against each other in a commonly owned game. A lot of other
interactions are also possible (e.g. watch your friend’s live broadcast when your friend is in a
game).  

**Tech Stack for this project:**  
Front End: Front End: Bootstrap 3  
Web framework: Django (website: https://www.djangoproject.com/)  
Programming Language: Python  
DBMS: SQLite  
  Defend against SQL Injections  
  Defend against XSS attacks  
  
**Source code:**  
models.py (Create database)  
create_table.sql (SQL corresponding to models.py)  
view.py (Implementation of all the website)  
templates/base.html (The base template of our website, used by other html files)  
templates/home.html (The home page template, used by view.py)  
templates/login.html (The login page template, used by view.py)  
templates/query*.html (The template page of query demo)  
tasks.py (The model for multi-thread method)  
data.py (The program that automatically extract data for new users)  

**Requirements:**  
Django 1.11 installed (website: https://www.djangoproject.com/)  
Python 3.5 installed  
Python Libraries:  
  steam library (pip install steam)  
  celery library (pip install celery)  
