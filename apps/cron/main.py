
import sys
from datetime                   import datetime
from os.path                    import abspath, dirname, join,split
from site                       import addsitedir

# Set up the environment to run on it own.
APP_ROOT, tail = split(abspath(dirname(__file__)))
PROJECT_ROOT, tail = split(APP_ROOT)

sys.path.insert(0,PROJECT_ROOT)
sys.path.insert(0,APP_ROOT)

from django.core.management     import setup_environ

import settings
setup_environ(settings)

# From here on through its treated as a normal django module
from django.contrib.auth.models     import User
from django.db.models               import Q
from django.template                import loader, Context

# Local libraries
from client                         import EventbriteClient
from base.models                    import *
from mail                           import Mailer
from meetup                         import MeetUpAPI
from social.models                  import MeetupProfile

"""
# Open SMTP emailer
mailer  = Mailer( server   = settings.EMAIL_HOST,
                  user     = settings.EMAIL_HOST_USER,
                  password = settings.EMAIL_HOST_PASSWORD
                )

"""
# Open Amazon emailer
mailer  = Mailer ( mailer = 'amazon',
                   access_key = settings.AMAZON['AccessKeyId'],
                   secret_key = settings.AMAZON['SecretKey']
                 )

def log(message):
    """
    Time stamp all messages
    """
    return datetime.today().strftime("%Y-%m-%d %H:%M")+ ' ' + message


def get_attendees( evb, event_id ):
    """
    Get all the attendees for an event from Eventbrite
    """
    attendee_list = []

    # Get all the attendees of each event (New York, Boston, Toronto ..)
    try:
        attendees = evb.list_event_attendees( event_id = int(event_id) )
    except:
        print log('Eventbrite Error: No attendees for event id ' + event_id )
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


def check_survey(attendee):
    """
     Return all the interests from the survey
    """
    if not 'answers' in attendee:
        return [], False

    leadbuyer = False

    # If so parse the survey answers and email attendee and sponser
    answers = attendee['answers']
    for answer in answers:
        if 'Check this box' in answer['answer']['question']:
            leadbuyer = True

        # Did they ask for help
        if 'Do you need help' in answer['answer']['question']:
            return answer['answer']['answer_text'].split('|'), leadbuyer

    # No survey answered
    return [], leadbuyer


def get_latest_events(evb, organizer_id, date = None):
    """
    Search for the latest events
    """
    try:
        events = evb.list_organizer_events(organizer_id = organizer_id)
    except:
        print log( 'Eventbrite Error: Events for ' + organizer_id )
        return []

    # Check if you get an error from Eventbrite
    if 'error' in events:
        print log( 'Eventbrite Error: ' +             \
                    events['error']['error_type'] +   \
                    ' for ' + str(organizer_id)
                  )
        return []

    # Compare to todays date and find all events ending after today
    if date == None:
        today = datetime.today()
    elif isinstance(date, datetime):
        today = date

    # Look through all events and keep all future events
    event_ids = []
    for event in events['events']:

        # Make sure these are not past events
        end_date = datetime.strptime(event['event']['end_date'],
                                     "%Y-%m-%d %H:%M:%S")
        delta = end_date - today

        # Only get next months events
        if delta.days >= 0:
            event_ids.append([ event['event']['title'],
                               event['event']['id'],
                               end_date
                              ]
                             )
    return event_ids

# Put latest event in the database
def database_events(organizer, evb = None):
    if evb == None:

        # Open a new Eventbrite client
        evb = EventbriteClient( app_key  = settings.EVENTBRITE['APP_KEY' ],
                                user_key = organizer.user_key     )

    # This is for testing
    date = datetime.strptime('2011-08-01', "%Y-%m-%d")

    # Get the latest from Eventbrite
    events = get_latest_events(evb, int(organizer.organizer_id) )
    event_list = []

    # Add each event and find the right organizer
    for event in events:
        try:
            event_rec = Event.objects.get( Q(event_id = event[1]) )
        except Event.DoesNotExist:
            event_rec = Event( event_id        = event[1],
                               describe        = event[0],
                               date            = event[2],
                               chapter         = organizer.chapter
                              )
            event_rec.save()

        event_list.append(event_rec)

    # Return the events list
    return event_list


# Generator to put the attendees in the database
def database_attendees( evb, event ):

    # Get all the attendees for the event from Eventbrite
    attendees = get_attendees( evb, event.event_id )

    # Add all attendees to the database
    for attendee in attendees:

        # Check if they are a user
        try:
            user = User.objects.get( Q(email = attendee['email']) )

        # If not create a new user
        except User.DoesNotExist:

            # Create a temporary password and username which is 30 chars max
            password = attendee['last_name']+'$'+attendee['first_name'],
            username = attendee['email'][0:30]
            user = User.objects.create_user(  username = username,
                                              email    = attendee['email'],
                                              password = password
                                            )
            user.first_name = attendee['first_name'].capitalize()
            user.last_name  = attendee['last_name'].capitalize()
            user.save()
            profile = Profile( user = user )
        else:
            profile = user.get_profile()

        # Update any profile changes
        profile.is_attendee = True

        if 'company' in attendee:
            profile.company = attendee['company']
        if 'cell_phone' in attendee:
            profile.phone = attendee['cell_phone']
        profile.save()

        # Return attendees who answered the survey
        interests, leadbuyer = check_survey( attendee )

        # If they checked they want leads they are a leadbuyer
        if leadbuyer:
            profile.is_leadbuyer = True
            profile.save()

        # Add the attendee with or with out interests to the event
        if len(interests) == 0:
            query = Survey.objects.filter( event = event,
                                           attendee = user
                                         )
            if query.count() == 0:
                survey  = Survey( event    = event,
                                  attendee = user
                                )
                survey.save()

            # Continue to the next attendee
            continue

        # If the user has interests checked return them
        surveys = []
        for interest in interests:

            # Normalize the interest and see if you have it
            interest = interest.lstrip().rstrip()
            normal_interest = Interest.objects.close_to( interest )

            # Is this a new interest?
            if normal_interest == None:
                print log( "New Interest: " + interest )
                Interest( interest = interest )

            try:
                survey = Survey.objects.get( event = event,
                                             interest = normal_interest,
                                             attendee = user
                                            )

            # If not create it with interests
            except Survey.DoesNotExist:
                survey  = Survey( event = event,
                                  interest = normal_interest,
                                  attendee = user
                                 )
                survey.save()
            surveys.append(survey)

        # Yield all the surveys for this user
        yield surveys

    return

MAX_SURVEY_SEND = 10
def make_contact( survey, deal, template ):
    for term in deal.terms():
        if not term.execute( event = survey.event ):
            continue

        # Don't spam user
        survey.mailed += 1
        survey.save()

        if survey.mails_for() > MAX_SURVEY_SEND:
            continue

        sponser   = term.buyer
        attendee  = survey.attendee
        event     = survey.event
        interest  = deal.interest
        organizer = survey.event.chapter.organizer

        c = Context({'interest' :interest,
                     'attendee' :attendee,
                     'sponser'  :sponser,
                     'organizer':organizer
                     })

        message = template.render(c)
        print_connection( attendee, sponser, interest )

        subject = survey.event.describe + '-' + interest.interest

        recipients = [ attendee.email,
                       sponser.email,
                       event.chapter.organizer.email ]

        # TESTING
        """
        recipients = ['pete.douma@gmail.com']
        mailer.email_to( message,
                         recipients,
                         'newsletter@brightmap.com',
                         subject
                        )
        """
def print_event(event):
    delta = event.date - datetime.today()
    print log('Event - ' +  event.describe + ' ' + str(delta.days) )

# Print the log message
def print_connection( attendee, sponser, interest ):
    print log(
               " Connecting: " +             \
               attendee.first_name + ' ' +   \
               attendee.last_name +  ' - ' + \
               attendee.email + ' with ' +   \
               sponser.first_name + ' ' +    \
               sponser.last_name + ' - ' +   \
               sponser.email +' for ' +      \
               interest.interest
              )

# This is the main routine
def main():
    # Get all organizers
    organizations = Organization.objects.filter()
    for organization in organizations:
        for chapter in organization.chapter_set.all():
            # Check for meetups
            """
            meetup = MeetUpAPI( user = chapter.organizer )
            if meetup:
                meetup.get_groups()
            """
            # Open a new Eventbrite client
            tickets = chapter.get_eventbrite()
            for ticket in tickets:
                app_key  = settings.EVENTBRITE['APP_KEY' ]
                user_key = ticket.user_key
                evb = EventbriteClient( app_key = app_key, user_key = user_key )

                #Get the email template for this organization
                letter = chapter.letter
                if letter != None:
                    template = loader.get_template(letter.letter)
                else:
                    template = loader.get_template( 'letters/default.tmpl' )

                # Get the attendess of each event < 30 day away for each city
                for event in database_events( ticket, evb ):

                    # Log the events
                    print_event(event)

                    # Put all attendees in the db, but only return those that
                    #     answered the survey
                    for surveys in database_attendees( evb, event ):

                        # For each interest match sponsers
                        for survey in surveys:
                            try:
                                deal = chapter.deal( survey.interest )

                            # This can happen if no deal for a survey item
                            except Deal.DoesNotExist:
                                print log( chapter.name +        \
                                           ' has no deal for ' + \
                                           survey.interest.interest
                                          )
                                continue

                            if event.add_connection( survey, deal ):
                                make_contact( survey, deal, template )

if __name__ == '__main__':
    main()
