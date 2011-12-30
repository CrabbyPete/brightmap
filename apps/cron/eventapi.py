from datetime                       import datetime
from termcolor                      import colored
from client                         import EventbriteClient

from settings                       import EVENTBRITE

""""
from meetup                         import MeetUpAPI
from social.models                  import MeetupProfile
"""
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


class GenericAPI(object):
    """
    Define the functions each interface must pform in a standard way
    """
    def connect(self):
        return
    
    def get_latest_events(self):
        """ Return the latest events that have not passed """
        return
    
    def get_attendees(self, event):
        """ Return the attendees to an event """
        return
    
    def check_survey(self, attendee ):
        """ Return surveys for attendees """
        return

class MeetUp(object):
    """ Meetup API Interface """


class EventBrite(object):
    """ Eventbrite API Interface """
    
    evb = None;
    
    def __init__( self, tokens, user_key ):           
        self.evb = EventbriteClient( tokens = tokens, user_key = user_key )
        
    
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
            """ Do not add leadbuyer automatically
            if 'Check this box' in answer['answer']['question']:
                leadbuyer = True
            """
            # Did they ask for help
            if 'Do you need help' in answer['answer']['question']:
                return answer['answer']['answer_text'].split('|'), leadbuyer

        # No survey answered
        return [], leadbuyer


    def get_latest_events( self, organizer_id ):
        
        """ Search for the latest events """
        try:
            events = self.evb.organizer_list_events({'id':organizer_id})
        except Exception:
            print log( 'Eventbrite Error: Events for ' + organizer_id )
            logger.debug('Eventbrite Error: Events for ' + organizer_id )
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
    api = EventBrite(  EVENTBRITE['APP_KEY'], 131405059418924847729 )
    api.get_latest_events( 953789113 )
    