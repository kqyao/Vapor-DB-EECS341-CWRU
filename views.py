from django.shortcuts import render, redirect, reverse

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import django.contrib.auth as auth

from django.contrib import messages

from django.conf import settings

from vapor.models import UserProfile, Player
from vapor.data import scrap_for_new_user
import vapor.tasks

from steam import WebAPI
import sqlite3

api = WebAPI(key = settings.STEAM_API_KEY)

def data_ready_reaquired(view):
    def decorated(request, *args, **kwargs):
        profile = UserProfile.objects.get(user=request.user)
        if profile.data_ready == 0:
            return redirect('vapor:setup')
        else:
            return view(request, *args, **kwargs)
    return decorated

def login(request):
    if request.user.is_authenticated():
        return redirect(reverse('vapor:home'))
    else:
        return render(request, 'login.html', {})

@login_required
def logout(request):
    auth.logout(request)
    return redirect('vapor:login')

def do_login_register(request):
    if request.user.is_authenticated():
        return redirect(reverse('vapor:home'))
    else:
        username = request.POST.get('inputUsername', None)
        password = request.POST.get('inputPassword', None)
        steamid = request.POST.get('inputSteamID', None)
        action = request.POST.get('action', None)
        if action is None:
            return redirect(reverse('vapor:login'))
        elif action == 'register':
            if username is None or password is None or steamid is None:
                messages.error(request, "Register failed, Missing Required field")
                return redirect('vapor:login')
            if steamid == '' or steamid == 'SteamID':
                messages.error(request, "Register failed, Missing SteamID")
                return redirect('vapor:login')

            if User.objects.filter(username=username).exists():
                messages.error(request, "Register failed, Username already taken!")
                return redirect('vapor:login')

            if UserProfile.objects.filter(steamid=steamid).exists():
                messages.error(request, "Register failed, steamID already used")
                return redirect('vapor:login')

            ret = api.ISteamUser.GetPlayerSummaries(steamids=steamid)
            if ret['response']['players'] == []:
                messages.error(request, "Register failed, invalid steamID")
                return redirect('vapor:login')

            data = ret['response']['players'][0]
            Player.objects.get_or_create(
                steamid = steamid,
                defaults= {
                    'playerName' : data['personaname'],
                    'profileurl' : data['profileurl'],
                    'avatar' : data['avatar'],
                }
            )
            user = User.objects.create_user(username, "null@null.com", password)
            profile = UserProfile.objects.create(user=user, steamid=steamid)

            auth.login(request, user)
            scrap_for_new_user(user)

            return redirect('vapor:home')
        elif action == 'login' :
            if username is None or password is None:
                messages.error(request, "Login Failed, Missing Username or Password")
                return redirect('vapor:login')
            user = authenticate(username = username, password = password)
            if user is not None:
                print(user.username + " signed in")
                auth.login(request, user)
                profile = UserProfile.objects.get(user=user)
                if profile.data_ready != 0:
                    return redirect('vapor:home')
                else:
                    return redirect('vapor:setup')
            else:
                messages.error(request, "Login Failed, non-existing user or wrong password")
                return redirect('vapor:login')
        else:
            messages.error(request, "Unknown action!")
            return redirect('vapor:login')

@login_required
@data_ready_reaquired
def user_home(request):
    title = "Curious about what's popular?"
    text = '''
    <h4>Steam</h4>
    <ul>
    <li>Steam by Valve is a game platform for vendors to sell game 
    as well as a gamer’s community.</li>
    <li>Players are able to “meet new people, join game groups, form clans,
     chat in-game and more” in this platform.</li> 
    </ul>
    <h4>Help Understand what's going on around <b>YOU</b></h4>
    <ul>
    <li> Get more information about your friend circle </li>
    <li> The popular games among your friends. </li>
    <li> The interesting groups your friends are in. </li> 
    <li> The achievements your friends get. </li>
    </ul>
    <h4> Developers of this project </h4>
    This project is developed by Yue YAO [yxy686] and Kaiqi YAO [kxy184]
    '''
    profile = UserProfile.objects.get(user=request.user)

    return render(request, 'home.html', {
        'profile' : profile,
        'homepage_text_title': title,
        'homepage_text_content': text,
        'homepage_image_url': "https://steamstore-a.akamaihd.net/public/shared/images/responsive/share_steam_logo.png",
    })

@login_required
def setup(request):
    profile = UserProfile.objects.get(user=request.user)
    if profile.data_ready != 0:
        return redirect('vapor:home')
    profile.data_load_remain = vapor.tasks.size()
    profile.save()
    return render(request,'setup.html', {
        'profile' : profile,
    })

def query1(request):
    steamID_param = request.POST.get('steamID')
    numOfGame_param = request.POST.get('numOfGame')
    if (steamID_param is None) or (steamID_param == ''):
        steamID_param = '76561198152495215'
    if (numOfGame_param is None) or (numOfGame_param == ''):
        numOfGame_param = '5'

    query_str = '''
SELECT P.appid_id, G.gameName
From vapor_plays P, vapor_game G
WHERE P.appid_id = G.appid AND
  P.steamid_id in (
  SELECT F.player2id_id
  FROM vapor_friends F
  WHERE F.player1id_id = ?
)
GROUP BY P.appid_id
HAVING count(P.steamid_id) >= ?'''
    qlist = []
    with sqlite3.connect("db.sqlite3") as con:
        c = con.cursor()
        results = c.execute(query_str, (steamID_param, int(numOfGame_param))).fetchall()
        qlist.append(
            {
                'steamid': steamID_param,
                'numofgame': numOfGame_param,
                'query_string': query_str,
                'query_parameter': (steamID_param, numOfGame_param),
                'result': results
            }
        )

    return render(request, 'query1.html', {
        'query_list': qlist,
        'steamID' : steamID_param,
        'numOfGame' : numOfGame_param,
    })

def query2(request):
    steamID_param = request.POST.get('steamID')
    numOfGame_param = request.POST.get('numOfGame')
    if (steamID_param is None) or (steamID_param == ''):
        steamID_param = '76561198152495215'
    if (numOfGame_param is None) or (numOfGame_param == ''):
        numOfGame_param = '2'

    query_str = '''
SELECT MO.groupid_id, G.groupName, G.summary, G.avatar
FROM vapor_groups G, vapor_memberof MO
WHERE g.groupid = MO.groupid_id AND
  MO.steamid_id in (
  SELECT F.player2id_id
  FROM vapor_friends F
  WHERE F.player1id_id = ?
)
GROUP BY MO.groupid_id
HAVING count(MO.steamid_id) >=?'''
    qlist = []
    with sqlite3.connect("db.sqlite3") as con:
        c = con.cursor()
        results = c.execute(query_str, (steamID_param, int(numOfGame_param))).fetchall()
        qlist.append(
            {
                'steamid': steamID_param,
                'numofgame': numOfGame_param,
                'query_string': query_str,
                'query_parameter': (steamID_param, numOfGame_param),
                'result': results
            }
        )

    return render(request, 'query2.html', {
        'query_list': qlist,
        'steamID' : steamID_param,
        'numOfGame' : numOfGame_param,
    })

def query3(request):
    steamID_param = request.POST.get('steamID')
    if (steamID_param is None) or (steamID_param == ''):
        steamID_param = '76561198152495215'

    query_str = '''
SELECT A.appid_id, A.achievementName, count(C.steamid_id)
FROM vapor_completes C, vapor_achievement A
WHERE A.id = C.achievementid_id AND
  C.steamid_id in (
  SELECT F.player2id_id
  FROM vapor_friends F
  WHERE F.player1id_id = ?
)
GROUP BY C.achievementid_id
ORDER BY count(C.steamid_id) DESC
LIMIT 20'''
    qlist = []
    with sqlite3.connect("db.sqlite3") as con:
        c = con.cursor()
        results = c.execute(query_str, (steamID_param,)).fetchall()
        qlist.append(
            {
                'steamid': steamID_param,
                'query_string': query_str,
                'query_parameter': (steamID_param,),
                'result': results
            }
        )

    return render(request, 'query3.html', {
        'query_list': qlist,
        'steamID' : steamID_param,
    })

def query4(request):
    steamID_param = request.POST.get('steamID')
    if (steamID_param is None) or (steamID_param == ''):
        steamID_param = '90'

    query_str = '''
SELECT DISTINCT P.steamid, P.playerName, P.avatar
FROM vapor_player P, vapor_completes C
WHERE P.steamid = C.steamid_id AND
  NOT EXISTS(
    SELECT *
    FROM vapor_achievement A
    WHERE A.id = C.achievementid_id AND
      A.globalCompletePercentage < ?
  )'''
    qlist = []
    with sqlite3.connect("db.sqlite3") as con:
        c = con.cursor()
        results = c.execute(query_str, (steamID_param,)).fetchall()
        qlist.append(
            {
                'steamid': steamID_param,
                'query_string': query_str,
                'query_parameter': (steamID_param,),
                'result': results
            }
        )

    return render(request, 'query4.html', {
        'query_list': qlist,
        'steamID' : steamID_param,
    })


def query5(request):
    query_str = '''
SELECT DISTINCT Player.steamid, Player.playerName, Player.avatar
FROM vapor_player Player
WHERE NOT EXISTS(
  SELECT *
  FROM vapor_plays Plays
  WHERE Plays.steamid_id = Player.steamid
)'''
    qlist = []
    with sqlite3.connect("db.sqlite3") as con:
        c = con.cursor()
        results = c.execute(query_str).fetchall()
        qlist.append(
            {
                'query_string': query_str,
                'query_parameter': (),
                'result': results
            }
        )

    return render(request, 'query5.html', {
        'query_list': qlist,
    })
