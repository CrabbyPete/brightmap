from django.db                  import models
from django.contrib.auth.models import User


class AuthToken(models.Model):
    user      	= models.ForeignKey(User)
    service		= models.CharField(max_length=100,   blank = True, null = True )
    token     	= models.CharField(max_length=100,   blank = True, null = True )
    refresh     = models.CharField(max_length=100,   blank = True, null = True )
    created   	= models.DateTimeField(auto_now = True)

    def __unicode__(self):
        return self.user.username+'-'+self.service

