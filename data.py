import xml.etree.ElementTree as ET
from django.conf import settings
from requests.exceptions import HTTPError
from threading import Thread

from vapor.models import *
import vapor.tasks as tasks

import urllib.request
from steam import WebAPI

api = WebAPI(key=settings.STEAM_API_KEY)

def scrap_user_info(steamid):
    userinfo = api.ISteamUser.GetPlayerSummaries(steamids=steamid)

def extract_group_info(group : Groups):
    print("Extacting group info for group %s" % group.groupid)

    gid = group.groupid

    url = "http://steamcommunity.com/gid/%s/memberslistxml/?xml=1" % gid

    try:
        response = urllib.request.urlopen(url)
    except:
        print(extract_group_info.__name__ +
              " | %s group his profile to private" % gid)
        return

    try:
        data = response.read()
        tree = ET.fromstring(data.decode('utf-8'))
    except:
        print(extract_group_info.__name__ +
              " | Error in parsing data for group %s " % gid)
        return

    group_name = tree.find('groupDetails/groupName').text
    group_headline = tree.find('groupDetails/headline').text
    group_summary = tree.find('groupDetails/summary').text
    group_avatar = tree.find('groupDetails/avatarFull').text

    group.groupName=group_name
    group.headline=group_headline
    group.summary=group_summary
    group.avatar=group_avatar
    group.isPrivate=False
    group.save()


def extract_group_membership(player : Player):

    print("Extacting group info for player %s" % player.steamid)

    url = 'http://steamcommunity.com/profiles/%s/?xml=1' % player.steamid
    try:
        response = urllib.request.urlopen(url)
    except:
        print(extract_group_membership.__name__ +
              " | %s sets his profile to private" % player.steamid)
        return
    try:
        data = response.read()
        tree = ET.fromstring(data.decode('utf-8'))
    except:
        print(extract_group_membership.__name__ +
              " | Error in parsing data for player %s " % player.steamid)
        return

    grouplist = tree.findall('groups/group')
    grouplist = [group.find('groupID64').text for group in grouplist]

    for gid in grouplist:
        group, create = Groups.objects.get_or_create(groupid=gid)
        if create:
            tasks.push_task(extract_group_info, group)
        MemberOf.objects.create(steamid=player, groupid=group)

def extract_complete_relationship(plays : Plays):

    player = plays.steamid
    steamid = player.steamid
    game = plays.appid
    appid = game.appid

    print("Extacting completes info for player %s and game %d" % (steamid, appid))

    try:
        completelist = api.ISteamUserStats.GetPlayerAchievements(
            steamid = steamid,
            appid = appid
        )
    except HTTPError as e:
        print(extract_complete_relationship.__name__ +
              " | Error in loading achievement for player %s " % player.steamid)
        return

    try:
        completelist = completelist['playerstats']['achievements']
    except KeyError as e:
        print(extract_complete_relationship.__name__ +
              " | Error in parsing achievement for player %s " % player.steamid)
        print(completelist)
        return

    for item in completelist:
        if item['achieved'] ==1:
            achievement_name = item['apiname']
            achievement = Achievement.objects.get(
                appid = game,
                achievementName=achievement_name
            )
            complete, create = Completes.objects.get_or_create(
                steamid = player,
                achievementid = achievement
            )


def extract_achievement_info(game : Game):

    print("Extacting achievement info for game %d" % game.appid)

    achievement_list = api.ISteamUserStats.GetGlobalAchievementPercentagesForApp(
        gameid = game.appid
    )
    achievement_list = achievement_list['achievementpercentages']['achievements']
    for achievement_info in achievement_list:
        achievement_name = achievement_info['name']
        achievement_percent = achievement_info['percent']

        achievement, create = Achievement.objects.get_or_create(
            appid=game,
            achievementName = achievement_name,
            globalCompletePercentage = achievement_percent
        )

    game.achievement_ready = True
    game.save()


def extract_game_ownership(player : Player):

    print("Extacting game info for player %s" % player.steamid)

    appid_list = api.IPlayerService.GetOwnedGames(
        steamid=player.steamid, appids_filter=0,
        include_played_free_games=True, include_appinfo=True
    )
    appid_list = appid_list['response']['games']
    for app_info in appid_list:
        appid = app_info['appid']

        base_url = "http://media.steampowered.com/steamcommunity/public/images/apps/%d/%s.jpg"
        name = app_info['name']
        icon = base_url % (appid, app_info['img_icon_url'])
        logo = base_url % (appid, app_info['img_logo_url'])

        game, create = Game.objects.get_or_create(
            appid=appid,
            defaults={
                'gameName' : name,
                'iconUrl' : icon,
                'logoUrl' : logo,
            }
        )

        Plays.objects.create(
            steamid=player, appid=game, playtime=app_info['playtime_forever']
        )

def scrap_friends(player :  Player):

    steamid = player.steamid
    print("Scraping friend of %s" % player.steamid)
    try:
        friends = api.ISteamUser.GetFriendList(steamid=steamid, relationship='friend')
    except HTTPError as e:
        print(scrap_friends.__name__ +
              " | %s sets his profile to private" % player.steamid)
        return

    friendlist = friends['friendslist']['friends']
    idlist = [f['steamid'] for f in friendlist]
    idlist = [id for id in idlist if not Player.objects.filter(steamid=id).exists()]
    idstr = ",".join(map(str, idlist))

    friend_data = api.ISteamUser.GetPlayerSummaries(steamids=idstr)
    friend_data = friend_data['response']['players']
    for friend in friend_data:
        f_steamid = friend['steamid']
        f_profileUrl = friend['profileurl']
        f_avatar = friend['avatar']
        f_name = friend['personaname']

        f, create = Player.objects.get_or_create(
            steamid=f_steamid, playerName=f_name,
            profileurl=f_profileUrl, avatar=f_avatar
        )

        Friends.objects.get_or_create(player1id=player, player2id=f)
        Friends.objects.get_or_create(player1id=f,      player2id=player)

    print("Done scraping friend of %s" % player.steamid)

def scrap_for_new_user(user : User):
    profile = UserProfile.objects.get(user=user)

    def runner(steamid):
        print("Begin loading data for username=%s" % user.username)
        print("Root SteamID=%s" % steamid)
        print("Acquiring List of friends:")

        player = Player.objects.get(steamid=steamid)

        player_list = [player]

        profile.data_load_phase = "Loading Friends of '%s'" % player.playerName
        profile.save()

        scrap_friends(player)



        friend_list = Friends.objects.filter(player1id=player).all()
        for friend in friend_list:
            player2 = friend.player2id
            tasks.push_task(scrap_friends, player2)

            player_list.append(player2)

        profile.data_load_phase = "Loading 2nd level of friends"
        profile.save()

        tasks.join()

        for player in player_list:
            tasks.push_task(extract_group_membership, player)
            tasks.push_task(extract_game_ownership, player)

        profile.data_load_phase = "Loading Group info for everyone"
        profile.save()
        tasks.join()

        game_list = Game.objects.filter(achievement_ready=False).all()


        for game in game_list:
            game.achievement_ready = True
            game.save()
            tasks.push_task(extract_game_ownership, game)

        profile.data_load_phase = "Loading achievements for games"
        profile.save()
        tasks.join()

        for game in game_list:
            tasks.push_task(extract_achievement_info, game)

        tasks.join()

        for game in game_list:
            plays_list = Plays.objects.filter(appid=game).all()
            for plays in plays_list:
                tasks.push_task(extract_complete_relationship, plays)

        profile.data_load_phase = "Loading achievements for everyone"
        profile.save()
        tasks.join()

        profile.data_load_phase = "Congrats! Done."
        profile.data_ready = True
        profile.save()
        print("Done loading data for username=%s" % user.username)

    t = Thread(target=runner, kwargs={'steamid': profile.steamid})
    t.daemon = True
    t.start()


def deleteall():
    Player.objects.filter().delete()
    Groups.objects.filter().delete()
    Game.objects.filter().delete()
    User.objects.exclude(username='admin').delete()
