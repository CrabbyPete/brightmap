import urllib
import json
import settings

import django_header


from social.models      import  MeetupProfile
from base.models        import  Organization


# Meetup JSON Encoding format
JSON_ENCODING = 'ISO-8859-1'

class MeetUpAPI(object):
        meetup = None
        
        def __init__(self, user):
            try:
                self.meetup = MeetupProfile.objects.get(user = user)
            except MeetupProfile.DoesNotExist:
                return None


        def refresh(self):
            refresh_url = 'https://secure.meetup.com/oauth2/access?'
            
            kwargs = dict( client_id      = settings.MEETUP['API_KEY'],
                           client_secret  = settings.MEETUP['APP_SECRET'],
                           grant_type     = 'refresh_token',
                           refresh_token  = self.meetup.refresh
                         )
            
            url = refresh_url + urllib.urlencode(kwargs)
            fil = urllib.urlopen(url)
            data = fil.read()
            response = json.loads(data, JSON_ENCODING )
            return response

        def get(self, what, **kwargs ):
            if not 'access_token' in kwargs:
                kwargs['access_token'] = self.meetup.token

            what = what+'.json'
            url = 'https://api.meetup.com' + what + "?" + urllib.urlencode(kwargs)

            fil = urllib.urlopen(url)
            data = fil.read()
            response = json.loads(data, JSON_ENCODING )
            return response

        def get_groups( self, meetup ):
            return   self.get( '/2/groups',
                               access_token = meetup.token,
                               member_id = meetup.member_id
                              )

        def get_member( self, meetup, member_id ):
            return   self.get(  '/2/member/%s'%(member_id,),
                                access_token = meetup.token
                             )

        def get_members( self, meetup, group_id ):
            return   self.get( '/2/profiles',
                                access_token = meetup.token,
                                group_id = group_id
                              )

        def get_events( self, meetup, group_id ):
            return   self.get( '/2/events',
                               access_token = meetup.token,
                               group_id = group_id
                              )

        def get_checkins( self, meetup, event_id ):
            return  self.get( '/2/checkins',
                                 access_token = meetup.token,
                                 event_id = event_id
                               )

        def get_rsvps( self, meetup, event_id ):
            return self.get( '/2/rsvps',
                              access_token = meetup.token,
                              event_id = event_id
                             )
         
def main():
    # Get all organizers
    organizations = Organization.objects.all()
    for organization in organizations:
        for chapter in organization.chapter_set.all():
            print chapter.name
            # Check for meetups
            meetup = MeetUpAPI( user = chapter.organizer )
            if meetup.meetup:
                try:
                    groups = meetup.get_groups(meetup.meetup)
                except Exception, e:
                    meetup.refresh()
                    continue
                
                for group in groups['results']:
                    print group['name']
                    events = meetup.get_events( meetup.meetup, group['id'] )
                    for event in events['results']:
                        print event['id']
                    
                    members = meetup.get_members(meetup.meetup, group['id'])
                    for member in members['results']:
                        if 'Pete Douma' in member['name']:
                            if member['role'] == 'Assistant Organizer':
                                break;
            
if __name__ == '__main__':
    main()