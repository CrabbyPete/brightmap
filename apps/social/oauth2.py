import json
import urllib
import urllib2


import settings
from models     import AuthToken

JSON_ENCODING = 'ISO-8859-1'

class OAuth2(object):

    def __init__( self, api_key, app_secret ):
        self.app_secret    = app_secret
        self.api_key       = api_key

    def register(self, user, callback = None):
        self.callback_url = callback

        save = self.save_request( user )
 
        # Step 1. Get a request token from Provider.
        
        url = self.authenticate_url + 'response_type=code&client_id='+self.api_key
#        url = url + '&oauth_token=' + self.api_key
        url = url + '&state='+str(save)
        return  url


    def callback(self,request):
        token = request.GET['code']
        db    = AuthToken.objects.get( pk = request.GET['state'] )

        data = dict ( code  = token,
                      client_secret   = self.app_secret,
                      client_id       = self.api_key,
                      grant_type      = 'authorization_code',
                      redirect_uri    = self.callback_url,
                     )
        data = urllib.urlencode( data )

        request = urllib2.Request(self.access_token_url, data )
        request = urllib2.urlopen( request )
        result  = request.read()
        result  = json.loads( result )

        if 'access_token' in result:
            return self.get_info(result,db)
        return

    def save_request ( self, user ):
        try: 
            db = AuthToken.objects.get( user = user, service = self.service )
        except AuthToken.DoesNotExist:
            db = AuthToken(user = user, service = self.service )
        db.save()
        return db.pk

    def is_registered( self, user ):
        try:
            db = AuthToken.objects.get(user = user, service = self.service)
        except AuthToken.DoesNotExist:
            return False
        
        if not db.token:
            return False
        
        self.access_token = db.token
        self.refresh_token = db.refresh
        return True

    def get_info( self, content, db ):
        self.access_token = content['access_token']
        db.token = self.access_token

        if 'refresh_token' in content:
            self.refresh_token = content['refresh_token']
            db.refresh = self.refresh_token
        db.save()

class EventbriteAPI(OAuth2):
        service           = 'eventbrite'

        authenticate_url  = 'https://www.eventbrite.com/oauth/authorize?'
        access_token_url  = 'https://www.eventbrite.com/oauth/token?'
        callback_url      = settings.SITE_BASE + '/social/eventbrite'
        rest_url         = 'https://www.eventbrite.com/'
        
        def get(self, what, **kwargs ):
            what = what+'.json'
            url = 'https://api.meetup.com' + what + "?" + urllib.urlencode(kwargs)

            data = urllib.urlopen(url).read()
            response = json.loads(data, JSON_ENCODING )
            if 'results' in response:
                return response['results']
            else:
                return response


class MeetUpAPI(OAuth2):
        service          = 'meetup'

        authenticate_url = 'https://secure.meetup.com/oauth2/authorize?'
        access_token_url = 'https://secure.meetup.com/oauth2/access?'
        rest_url         = 'https://api.meetup.com'

 


        def get(self, what, **kwargs ):
            what = what+'.json'
            url = 'https://api.meetup.com' + what + "?" + urllib.urlencode(kwargs)

            data = urllib.urlopen(url).read()
            response = json.loads(data, JSON_ENCODING )
            if 'results' in response:
                return response['results']
            else:
                return response

        def post(self, what, **kwargs ):
            what = what+'.json'
            url = 'https://api.meetup.com' + what
            data = urllib.urlencode(kwargs)
            fil  = urllib.urlopen(url,data)
            data = fil.read()
            response = json.loads(data, JSON_ENCODING )
            if 'results' in response:
                return response['results']
            else:
                return response

        def account( self ):
            return self.get('/account',
                             access_token = self.access_token
                            )

        def get_groups( self, member_id ):
            return   self.get( '/2/groups',
                               access_token = self.access_token,
                               member_id    = member_id
                              )

        def get_member( self, member_id ):
            return   self.get(  '/2/member/%s'%(member_id,),
                                access_token = self.access_token
                             )

        def get_members( self, group_id ):
            return   self.get( '/2/profiles',
                                access_token = self.access_token,
                                group_id = group_id
                              )

        def get_events( self, group_id ):
            return   self.get( '/2/events',
                               access_token = self.access_token,
                               group_id = group_id
                              )

        def get_checkins( self, event_id ):
            return  self.get( '/2/checkins',
                                 access_token = self.access_token,
                                 event_id = event_id
                               )

        def get_rsvps( self, event_id ):
            return self.get( '/2/rsvps',
                              access_token = self.access_token,
                              event_id = event_id
                             )

        def post_message (self, member_id, subject, message ):
            return self.post( '/2/message',
                              access_token = self.access_token,
                              member_id = member_id,
                              message = message,
                              subject = subject
                            )


