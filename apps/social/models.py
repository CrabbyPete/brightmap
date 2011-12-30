from django.db                  import models
from django.contrib.auth.models import User


class AuthToken(models.Model):
    user      	= models.ForeignKey(User)
    service		= models.CharField(max_length=100,   blank = True, null = True )
    token     	= models.CharField(max_length=100,   blank = True, null = True )
    secret    	= models.CharField(max_length=100,   blank = True, null = True )
    created   	= models.DateTimeField(auto_now = True)
    session     = models.CharField(max_length=100,   blank = True, null = True )

    def __unicode__(self):
        return self.user.username+'-'+self.service

class SocialProfile(models.Model):
    user        = models.ForeignKey(User)
    secret      = models.CharField(max_length=100,   blank = True, null = True )
    token       = models.CharField(max_length=100,   blank = True, null = True )
    refresh     = models.CharField(max_length=100,   blank = True, null = True )
    expires     = models.IntegerField(               blank = True, null = True )

    def __unicode__(self):
        return self.user.email

class LinkedInProfile(SocialProfile):
    industry    = models.CharField(max_length=100,   blank = True, null = True )
    location    = models.CharField(max_length=100,   blank = True, null = True )
    title       = models.CharField(max_length=100,   blank = True, null = True )
    company     = models.CharField(max_length=100,   blank = True, null = True )
    summary     = models.TextField(                  blank = True, null = True )

class FaceBookProfile(SocialProfile):
    user_id     = models.CharField(max_length=100,   blank = True, null = True )
    photo       = models.URLField()

class TwitterProfile(SocialProfile):
    user_id     = models.CharField(max_length=100,   blank = True, null = True )
    screen_name = models.CharField(max_length=100,   blank = True, null = True )

class GoogleProfile(SocialProfile):
    pass

class MeetupProfile(SocialProfile):
    member_id    = models.CharField(max_length=100,  blank = True, null = True )

"""
class EventBriteProfile(SocialProfile):
    pass
"""