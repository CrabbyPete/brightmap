import pdb
import cgi
import simplejson as json
import urllib

import django_header


from social.models      import  MeetupProfile
from base.models        import *


# Meetup JSON Encoding format
JSON_ENCODING = 'ISO-8859-1'

import settings
PROMPT = False

class MeetUpAPI(object):
        def __init__(self, user):
            try:
                self.meetup = MeetupProfile.objects.get(user = user)
            except MeetupProfile.DoesNotExist:
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
        
def main():
    # Get all organizers
    organizations = Organization.objects.all()
    for organization in organizations:
        for chapter in organization.chapter_set.all():
            # Check for meetups
            meetup = MeetUpAPI( user = chapter.organizer )
            if meetup:
                meetup.get_groups()
            
import optparse
if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    # Add options for debugging
    op.add_option('-d', action="store_true", help = 'Debug no emails sent')
    op.add_option('-p', action="store_true", help = 'Prompt to send')

    opts,args = op.parse_args()

    # Check if options were set
    if opts.d:
        DEBUG = False
    else:
        DEBUG = True

    if opts.p:
        PROMPT = True
    else:
        PROMPT = False
    main()