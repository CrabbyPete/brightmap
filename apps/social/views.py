# Python
import pdb
import settings
import cgi
import urllib
import re

import oauth2   as oauth
import oauth2.clients.imap as imaplib


# Django
from django.utils                   import simplejson       as json
from django.http                    import HttpResponseRedirect
from django.contrib                 import auth
from django.contrib.auth.models     import User
from django.utils                   import simplejson

# Project
from models                         import AuthToken,      \
                                           TwitterProfile, \
                                           GoogleProfile,  \
                                           LinkedInProfile,\
                                           FaceBookProfile,\
                                           MeetupProfile

from facebook                       import GraphAPI

class OauthView(object):

    request_token_url = None
    access_token_url  = None
    authenticate_url  = None
    call_back_url	  = None
    rest_url          = None
    scope             = None

    def __init__(self, api_key, app_secret, **kwargs ):
        self.consumer  = oauth.Consumer(api_key, app_secret)
        self.client    = oauth.Client(self.consumer)
        if 'scope' in kwargs:
            self.scope = kwargs['scope']

    def __call__(self, request):
        if 'oauth_token' in request.GET:
            return self.callback( request )
        else:
            return self.register( request )


    def register(self,request):
        # Step 1. Get a request token from Provider.
        body = 'oauth_callback='+self.call_back_url
        if self.scope != None:
            # body += self.scope.strip()
            body +=  '&scope=%s' % re.sub( '\s', '+', 
                                           re.sub('\s+',  ' ',self.scope.strip())
                                         ) 
  
        resp, content = self.client.request( self.request_token_url,
                                             "POST", body = body   )
        if resp['status'] != '200':
            raise Exception("Invalid response from Provider.")

        # Step 2. Store the request token in a session for later use.
        data = dict(cgi.parse_qsl(content))

        # Step 3. Redirect the user to the authentication URL.
        if 'xoauth_request_auth_url' in data:
            url = "%s?oauth_token=%s" % ( data['xoauth_request_auth_url'],
                                          data['oauth_token']             )
        else:
            url = "%s?oauth_token=%s" % ( self.authenticate_url,
                                          data['oauth_token'] )



        # Save the data for the callback if the user is logged in
        if not request.user.is_anonymous():
            db = AuthToken ( user = request.user,
                             service = self.service,
                             token   = data['oauth_token'],
                             secret  = data['oauth_token_secret'])

            db.session = request.session.session_key

            db.save()
        return HttpResponseRedirect(url)

    def callback(self, request):
        # Get the token restore the session and delete the record
        db = AuthToken.objects.get(token =  request.GET['oauth_token'])
        session = db.session
        request.COOKIES['sessionid'] = session
        db.delete()

        token = oauth.Token( db.token, db.secret )
        # Step 1. Use the request token in the session to build a new client.
        if 'oauth_verifier' in request.GET:
            token.set_verifier(request.GET['oauth_verifier'])

        self.client = oauth.Client(self.consumer, token)

        # Step 2. Request the authorized access token from Provider.
        resp, content = self.client.request(self.access_token_url, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response from Provider.")

        # self.access_token = dict(cgi.parse_qsl(content))
        return self.get_info( db.user, dict(cgi.parse_qsl(content)))

    # Override this for each profile
    def get_info(self, user, content):
        return HttpResponseRedirect('/')


class OauthTwitter(OauthView):
        service           = 'twitter'
        request_token_url = 'https://api.twitter.com/oauth/request_token'
        access_token_url  = 'https://api.twitter.com/oauth/access_token'
        authenticate_url  = 'http://twitter.com/oauth/authorize'

        call_back_url	  = settings.SITE_BASE + '/social/twitter'

        def get_info( self, user, content ):
            try:
                user = User.objects.get(pk = user.id)
            except User.DoesNotExist:
                pass

            try:
                profile = TwitterProfile.objects.get(user = user)
            except TwitterProfile.DoesNotExist:
                profile = TwitterProfile(user = user)

            profile.token       = content['oauth_token']
            profile.secret      = content['oauth_token_secret']
            profile.user_id     = content['user_id']
            profile.screen_name = content['screen_name']

            profile.save()

            return  HttpResponseRedirect('/')

        def access(self, **kwargs):
            return  HttpResponseRedirect('/')

class OauthGoogle(OauthView):
        service           = 'google'
        request_token_url = 'https://www.google.com/accounts/OAuthGetRequestToken'
        access_token_url  = 'https://www.google.com/accounts/OAuthGetAccessToken'
        authorization_url = 'https://www.google.com/accounts/OAuthAuthorizeToken'
        call_back_url	  = settings.SITE_BASE + '/social/google'


        def register(self, request):
            kwargs = dict()
            kwargs['scope'] = self.scope

            req = oauth.Request.from_consumer_and_token( self.consumer,
                                                         http_url = self.request_token_url,
                                                         parameters = kwargs               )

            req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), self.consumer, None)
            data = urllib.urlencode(req)

            url='%s?%s'%(self.request_token_url, data)
            response = urllib.urlopen(url)
            data = response.read()
            data2 = dict(cgi.parse_qsl(data))

            db = AuthToken ( user = request.user,
                             service = self.service,
                             token   = data2['oauth_token'],
                             secret  = data2['oauth_token_secret'] )
            db.session = request.session.session_key
            db.save()

            token = oauth.Token.from_string(data)
            data = oauth.Request.from_token_and_callback( token = token,
                                                          callback=self.call_back_url,
                                                          http_url=self.authorization_url,)

            data = urllib.urlencode(data)
            url='%s?%s'%(self.authorization_url, data)

            return HttpResponseRedirect(url)

        def get_info( self, user, content ):
            try:
                user = User.objects.get(pk = user.id)
            except User.DoesNotExist:
                pass

            try:
                profile = GoogleProfile.objects.get(user = user)
            except GoogleProfile.DoesNotExist:
                profile = GoogleProfile(user = user)

            profile.token       = content['oauth_token']
            profile.secret      = content['oauth_token_secret']

            profile.save()

            return  HttpResponseRedirect('/')


class OauthLinkedIn(OauthView):
        service           = 'linkedin'
        request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken'
        access_token_url  = 'https://api.linkedin.com/uas/oauth/accessToken'
        authenticate_url  = 'https://www.linkedin.com/uas/oauth/authenticate'

        call_back_url      = settings.SITE_BASE + '/social/linkedin'
        rest_url          = 'http://api.linkedin.com/v1'


        def get_info( self, user, content ):
            headers = {'x-li-format':'json'}
            items = "(id,first-name,last-name,industry,summary,positions,location)"
            url = self.rest_url+ "/people/~:" + items

            token = oauth.Token( content['oauth_token'],
                                 content['oauth_token_secret'])

            client = oauth.Client(self.consumer,token)
            resp, data = client.request(url, "GET", headers=headers)
            if resp['status'] == '200':
                linkedin_profile = json.loads(data)
                try:
                    user = User.objects.get(pk = user.id)
                except User.DoesNotExist:
                    pass

                user.first_name = linkedin_profile['firstName']
                user.last_name  = linkedin_profile['lastName']

                try:
                    profile = LinkedInProfile.objects.get(user = user)
                except LinkedInProfile.DoesNotExist:
                    profile = LinkedInProfile(user = user)

                # Save our permanent token and secret for later.
                profile.token  = content['oauth_token']
                profile.secret = content['oauth_token_secret']

                profile.industry    = linkedin_profile['industry']
                profile.summary     = linkedin_profile['summary']
                profile.location    = linkedin_profile['location']['name']

                for position in linkedin_profile['positions']['values']:
                    if position['isCurrent']:
                        profile.title = position['title']
                        profile.company = position['company']['name']

                user.save()
                profile.save()

            return  HttpResponseRedirect('/')

class OauthMeetup(OauthView):
        service           = 'meetup'
        request_token_url = 'https://api.meetup.com/oauth/request/'
        access_token_url  = 'https://api.meetup.com/oauth/access/'
        authenticate_url  = 'http://www.meetup.com/authenticate/'
        refresh_url       = 'https://secure.meetup.com/oauth2/access?'
        scope             = 'basic+messaging'
        rest_url          = 'http://api.meetup.com/'
        call_back_url     = settings.SITE_BASE + '/social/meetup'


        def get_info( self, user, content ):
            try:
                user = User.objects.get(pk = user.id)
            except User.DoesNotExist:
                pass

            try:
                profile = MeetupProfile.objects.get(user = user)
            except MeetupProfile.DoesNotExist:
                profile = MeetupProfile(user = user)

            profile.token       = content['oauth_token']
            profile.secret      = content['oauth_token_secret']
            if 'member_id' in content:
                profile.member_id = content['member_id']

            if 'expire' in content:
                pass

            if 'refresh_token' in content:
                pass

            profile.save()
            return  HttpResponseRedirect('/')

        def refresh(self, api_key, app_secret, user, **kwargs):
            try:
                profile = MeetupProfile.objects.get(user = user)
            except MeetupProfile.DoesNotExist:
                return None





twitter  = OauthTwitter( settings.TWITTER['API_KEY'], settings.TWITTER['APP_SECRET'] )
linkedin = OauthLinkedIn( settings.LINKEDIN['API_KEY'], settings.LINKEDIN['APP_SECRET'] )
google   = OauthGoogle( settings.GOOGLE['API_KEY'], settings.GOOGLE['APP_SECRET'],scope='https://mail.google.com/' )
meetup   = OauthMeetup( settings.MEETUP['API_KEY'], settings.MEETUP['APP_SECRET']  )

def gmail(request):
    try:
        g = GoogleProfile.objects.get(user = request.user)
    except GoogleProfile.DoesNotExist:
        pass
    else:
        url = "https://mail.google.com/mail/b/%s/imap/" % request.user.email

        token = oauth.Token(g.token, g.secret)

        conn = imaplib.IMAP4_SSL('imap.googlemail.com')
        #conn.debug = 4
        try:
            conn.authenticate(url, google.consumer, token)
        except:
            pass
        else:
            conn.select('INBOX')
            ok, mess = conn.search(None, "UNDELETED")

    return  HttpResponseRedirect('/')

# /2/events args = member_id

def meet_request(request):
    path = '2/events'
    user = request.user

    profile = MeetupProfile.objects.get(user = user)

    args = { 'access_token':profile.token,
             'member_id'   :profile.member_id }

    rest_url = 'https://api.meetup.com/'

    url = rest_url + path + "?" + urllib.urlencode(args)
    file = urllib.urlopen( url )
    try:
        result = file.read()
        response = simplejson.loads(result)
    except:
        pass
    finally:
        file.close()

    #return response
    return  HttpResponseRedirect('/')

# Facebooks oauth is different than others so use this.
# Allow user to login with Facebook. This will get call 3 times if the chooses Facebook logon
def facebook( request ):
    user = request.user
    parms = { 'client_id': settings.FACEBOOK['APP_ID'],
              'redirect_uri': settings.SITE_BASE + request.path
            }

    # You will get this from Facebook calling you back
    if 'code' in request.GET:
        parms['client_secret'] = settings.FACEBOOK['APP_SECRET']
        parms['code'] = request.GET['code']

        url = 'https://graph.facebook.com/oauth/access_token?' + urllib.urlencode(parms)
        response = cgi.parse_qs( urllib.urlopen(url).read() )

        if 'access_token' in response:
            access_token = response['access_token'][0]
            graph   = GraphAPI( access_token )
            me      = graph.get_object("me")
            picture = graph.request('me',{'fields':'picture'})

            try:
                user = User.objects.get(email = me['email'])
            except User.DoesNotExist:
                password = me['id']
                user  = User.objects.create_user( username = me['name'],
                                                  email    = me['email'],
                                                  password = password
                                                 )

                user.first_name = me[u'first_name']
                user.last_name= me[u'last_name']
                user.save()

                profile = FaceBookProfile(user = user, facebook_id = me[u'id'])

            else:
                profile = FaceBookProfile.objects.get(user = user)


            profile.photo = picture['picture']
            profile.token = access_token

            profile.save()

            user = auth.authenticate(username = user.username, password = password )
            if user != None and user.is_active:
                auth.login(request, user)

            url = '/'

    # This gets called by the user hitting the Facebook logon button
    else:
        parms['scope'] = 'email,publish_stream'
        url = "https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(parms)

    return HttpResponseRedirect(url)