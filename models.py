from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Log(models.Model):
    message = models.CharField(max_length=200, null=False)

    def __str__(self):
        return self.message

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    steamid = models.CharField(max_length=20)
    data_ready = models.IntegerField(default=0)
    data_load_remain = models.IntegerField(default=0)
    data_load_phase = models.CharField(max_length=100, default='Initializing')

    def __str__(self):
        return str(self.user) + ", SteamID = "+ self.steamid

class Player(models.Model):
    steamid = models.CharField(max_length=20, primary_key=True)
    playerName = models.CharField(max_length=50)
    profileurl = models.CharField(max_length=200, null=True)
    avatar = models.CharField(max_length=200, null=True)
    data_ready = models.BooleanField(null=False, default=False)

    def __str__(self):
        return self.playerName + " " + self.steamid

class Friends(models.Model):
    player1id = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="player1")
    player2id = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="player2")

    def __str__(self):
        return str(self.player1id) + " <--> " + str(self.player2id)

class Groups(models.Model):
    groupid = models.CharField(max_length=20, primary_key=True)
    isPrivate = models.BooleanField(null=False, default=True)
    groupName = models.CharField(max_length=50, null=True)
    headline = models.CharField(max_length=200, null=True)
    summary = models.CharField(max_length=500, null=True)
    avatar = models.CharField(max_length=200, null=True)
    def __str__(self):
        return str(self.groupid) + " / " + str(self.groupName)

class MemberOf(models.Model):
    steamid = models.ForeignKey(Player, on_delete=models.CASCADE)
    groupid = models.ForeignKey(Groups, on_delete=models.CASCADE)


    def __str__(self):
        return str(self.steamid) + " @ " + str(self.groupid)

class Game(models.Model):
    appid = models.IntegerField(primary_key=True)
    gameName = models.CharField(max_length=50, null=True)
    iconUrl = models.CharField(max_length=200, null=True)
    logoUrl = models.CharField(max_length=200, null=True)
    achievement_ready = models.BooleanField(null=False, default=False)

    def __str__(self):
        return str(self.appid) + " / " + self.gameName

class Plays(models.Model):
    steamid = models.ForeignKey(Player, on_delete=models.CASCADE)
    appid = models.ForeignKey(Game, on_delete=models.CASCADE)
    playtime = models.IntegerField(null=True)

    class Meta:
        unique_together = (("steamid", "appid"),)

    def __str__(self):
        return str(self.steamid) + " -> " + self.appid.gameName

class Achievement(models.Model):
    appid = models.ForeignKey(Game, on_delete=models.CASCADE)
    achievementName = models.CharField(max_length=100, null = True)
    globalCompletePercentage = models.FloatField(null=True)
    class Meta:
        unique_together = (("appid", "achievementName"),)

    def __str__(self):
        return str(self.appid) + self.achievementName

class Completes(models.Model):
    steamid = models.ForeignKey(Player, on_delete=models.CASCADE)
    achievementid = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    class Meta:
        unique_together = (("steamid", "achievementid"),)

    def __str__(self):
        return str(self.steamid) +" <- "+ str(self.achievementid)