from datetime                       import datetime
from termcolor                      import colored
from eventbrite.client              import EventbriteClient

from settings                       import EVENTBRITE

import logging
logger = logging.getLogger('main.py')


def log(message, color = None):
    """
    Time stamp all messages
    """
    string = datetime.today().strftime("%Y-%m-%d %H:%M")+ ',  ' + message
    if color:
        string = colored(string, color )
        
    return string


class EventBrite(object):
    """ Eventbrite API Interface """
    
    evb = None;
    
    def __init__( self, app_key = None, user_key = None, access_token = None ):
        if not access_token:           
            self.evb = EventbriteClient( {'app_key':app_key, 'user_key':user_key} )
        else:
            self.evb = EventbriteClient( {'access_code':access_token} )
    
    
    def get_organizers(self):
        try:
            organizers = self.evb.user_list_organizers()
        except Exception, e:
            return []
        
        organizer_list = []
        
        for organizer in organizers['organizers']:
            organizer_list.append(organizer['organizer']['id'])
        return organizer_list
    
    def get_attendees( self, event_id ):
        """ Get all the attendees for an event from Eventbrite """
        
        attendee_list = []
 
        # Get all the attendees of each event (New York, Boston, Toronto ..)
        try:
            attendees = self.evb.event_list_attendees( {'id': event_id} )
        except Exception, e:
            print log('Eventbrite Error: '+ str(e) +" for event id:" + str(event_id) )
            return []

        if 'error' in attendees:
            print log( 'Eventbrite Error: ' + attendees['error']['error_message'] +
                       ' event id ' + str( event_id )
                 )
            return []

        # Append attendee interests note:Eventbrite adds redundant levels
        for attendee in attendees['attendees']:
            attendee_list.append( attendee['attendee'] )

        return attendee_list


    def check_survey(self, attendee):
        """ Return all the interests from the survey """
        if not 'answers' in attendee:
            return [], False

        leadbuyer = False

        # If so parse the survey answers and email attendee and sponser
        answers = attendee['answers']
        for answer in answers:
            if 'Check this box' in answer['answer']['question']:
                leadbuyer = True
            elif 'Become a preferred service provider' in answer['answer']['question']:
                leadbuyer = True
                
        # Did they ask for help Note: two pass because never know where the answer is. 
        for answer in answers:
            if 'Do you need help' in answer['answer']['question']:
                return answer['answer']['answer_text'].split('|'), leadbuyer

        # No survey answered
        return [], leadbuyer


    def get_latest_events( self, organizer_id = None ):
        
        """ Search for the latest events """
        param = {}
        if organizer_id:
            param = {'id':organizer_id }
        try:
            events = self.evb.organizer_list_events(param)
        except Exception, e:
            print log( 'Eventbrite Error:%s for %u'%(e, organizer_id ) )
            logger.debug( 'Eventbrite Error:%s for %u'%(e, organizer_id ) )
            return []

        # Check if you get an error from Eventbrite
        if 'error' in events:
            err = 'Eventbrite Error: ' + events['error']['error_type'] + ' for ' + str(organizer_id)
            print log( err, 'red' )
            #logger.debug( err )
            return []


        # Look through all events and keep all future events after today
        event_ids = []
        for event in events['events']:
            if event['event']['status'] != 'Live':
                continue

            # Make sure these are not past events
            start_date = datetime.strptime( event['event']['start_date'],
                                            "%Y-%m-%d %H:%M:%S"
                                          )
        
            end_date   = datetime.strptime( event['event']['end_date'],
                                            "%Y-%m-%d %H:%M:%S"
                                          )
        
            # Check if this is multi-day
            if start_date != end_date:
                end_date = start_date
        
            # Only get future events
            if end_date < datetime.today():
                continue

            event_ids.append([ event['event']['title'],
                               event['event']['id'],
                               end_date
                             ]
                            )
        return event_ids
    
if __name__ == '__main__':
    api = EventBrite(  EVENTBRITE['APP_KEY'], 132551334525168952013 )
    api.get_latest_events( 1171027209 )
    