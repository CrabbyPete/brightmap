import pdb
import cgi
import json
import urllib

from social.models      import  MeetupProfile

# Meetup JSON Encoding format
JSON_ENCODING = 'ISO-8859-1'

import settings

class MeetUpAPI(object):
        def __init__(self, user):
            try:
                self.meetup = MeetupProfile.objects.get(user = user)
            except MeetUpProfile.DoesNotExist:
                return None


        def refresh(self):
            refresh_url = 'https://secure.meetup.com/oauth2/access?'
            kwargs = { client_id     : settings.MEETUP['API_KEY'],
                       client_secret : settings.MEETUP['APP_SECRET'],
                       grant_type    : 'refresh_token',
                       refresh_token : meetup.refresh
                      }
            url = refresh_url + urllib.urlencode(kwargs)
            file = urllib.urlopen(url)
            data = file.read()
            response = json.loads(data, JSON_ENCODING )
            return response

        def get(self, what, **kwargs ):
            if not 'access_token' in kwargs:
                kwargs['access_token'] = self.meetup.token

            what = what+'.json'
            url = 'https://api.meetup.com' + what + "?" + urllib.urlencode(kwargs)

            file = urllib.urlopen(url)

            data = file.read()
            response = json.loads(data, JSON_ENCODING )
            return response

        def get_groups( self ):
            groups = self.get( '/2/groups',
                               access_token = self.meetup.token,
                               member_id = self.meetup.member_id
                              )

            for group in groups['results']:

                print group['name'] + ' = ' + str(group['id'])
                if group['id'] == 1556336:
                    events = self.get( '/2/events',
                                       access_token = self.meetup.token,
                                       group_id = group['id']
                                      )

                    for event in events['results']:
                        rsvps = self.get( '/ew/rsvps',
                                          access_token = self.meetup.token,
                                          event_id = event['id']
                                         )
                    """
                    members = self.get( '/2/profiles',
                                        access_token = self.meetup.token,
                                        group_id = group['id']
                                       )
                    for member in members['results']:
                        print member['name'] + ':' + str(member['member_id'])
                    """
            return

