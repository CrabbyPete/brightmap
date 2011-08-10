
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
from django.core.mail               import send_mail,EmailMessage, \
                                           EmailMultiAlternatives
# Local libraries
from client                         import EventbriteClient
from base.models                    import *

# Get all the attendees for an event from Eventbrite
def get_attendees( evb, event_id ):
    attendee_list = []

    # Get all the attendees of each event (New York, Boston, Toronto ..)
    attendees = evb.list_event_attendees( event_id = int(event_id) )
    if 'error' in attendees:
        print attendees['error']['error_message']
        return []

    # Append attendee interests note:Eventbrite adds redundant levels
    for attendee in attendees['attendees']:
        attendee_list.append( attendee['attendee'] )

    return attendee_list

# Return all the interests from the survey
def check_survey(attendee):
    if not 'answers' in attendee:
        return []

    # If so parse the survey answers and email attendee and sponser
    answers = attendee['answers']
    for answer in answers:

        # Did they ask for help
        if 'Do you need help' in answer['answer']['question']:
            return answer['answer']['answer_text'].split('|')

    # No survey answered
    return []

def get_latest_events(evb, organizer_id, date = None):
    # Search for the latest event
    events = evb.list_organizer_events(organizer_id = organizer_id)

    # Compare to todays date and find all events ending after today
    if date != None:
        today = date
    else:
        today = datetime.today()

    # Check if this is right for errors
    if 'errors' in events:
        print Error + events['errors']
        return []

    # Look through all events
    event_ids = []
    for event in events['events']:

        # Make sure these are not past events
        end_date = datetime.strptime(event['event']['end_date'], "%Y-%m-%d %H:%M:%S")
        delta = end_date - today

        # This assumes monthly meetings and meetings are 30 days apart
        if delta.days >= 0 and delta.days < 30:
            event_ids.append([event['event']['title'],event['event']['id'],end_date])
            print today.strftime("%Y-%m-%d %H:%M") + ' ' +\
                  event['event']['title'] + " " + str(delta.days)

    return event_ids

# Put latest event in the database
def database_events(organizer, evb = None):
    if evb == None:

        # Open a new Eventbrite client
        evb = EventbriteClient( app_key  = settings.EVENTBRITE['APP_KEY' ],
                                user_key = organizer.user_key     )

    # This is for testing
    date = datetime.strptime('2011-06-01', "%Y-%m-%d")

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
def database_attendees(evb, event):

    # Get all the attendees for the event from Eventbrite
    attendees = get_attendees( evb, event.event_id )

    # Add all attendees to the database
    for attendee in attendees:

        try:
            user = User.objects.get( Q(email = attendee['email']) )
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

        profile.is_attendee = True

        # Update any profile changes
        if 'company' in attendee:
            profile.company = attendee['company']
        if 'cell_phone' in attendee:
            profile.phone = attendee['cell_phone']
        profile.save()

        # Add the user to the list if not in attendee list already
        event.attendees.add(user)

        # Return attendees who answered the survey
        interests = check_survey( attendee )


        yield user, interests

    return

# This is essentially send_mail, but adds attachments.
def mail_to(subject, message, from_email, recipient_list, attachments = None ):

    mail = EmailMessage(subject, message, from_email, recipient_list )
    if attachments != None:
        for attach in attachments:
            mail.attach_file(attach)
    #mail.send()

def make_contact( event, interest, deal, attendee, template ):
    terms = Term.objects.filter( deal = deal )
    for term in terms:
        if not term.execute(event = event):
            continue

        sponser = term.buyer
        today = datetime.today()
        c = Context({'interest':interest,
                     'attendee':attendee,
                     'sponser':sponser,
                     'organizer':event.chapter.organizer
                     })

        message = template.render(c)
        print today.strftime("%Y-%m-%d %H:%M")+ \
                             " Connecting: " +                \
                             attendee.first_name + ' ' +      \
                             attendee.last_name +  ' - ' +    \
                             attendee.email + ' with ' +      \
                             sponser.first_name + ' ' +       \
                             sponser.last_name+ ' - ' +       \
                             sponser.email +' for ' +         \
                             interest

        subject = event.describe + '-' + interest
        recipients = [ attendee.email, sponser.email,
                       event.chapter.organizer.email ]
        mail_to( subject, message, event.chapter.organizer.email, recipients)


# This is the main routine
def main():

    # Get the mail
    #mailbox = MailBox()
    #mailbox.login('fish@spotburn.com','fishf00l')

    # Get all organizers
    organizations = Organization.objects.filter()
    for organization in organizations:
        chapters = Chapter.objects.filter(organization = organization)
        for chapter in chapters:
            # Open a new Eventbrite client
            tickets = chapter.get_eventbrite()
            for ticket in tickets:
                evb = EventbriteClient( app_key  = settings.EVENTBRITE['APP_KEY' ],
                                        user_key = ticket.user_key     )

                #Get the email template for this organization
                letter = chapter.letter
                if letter != None:
                    template = loader.get_template(letter.letter)
                else:
                    template = loader.get_template_from_string(
                            '/media/letters/Ultra Light Startups (New York).tmp')

                # Get the attendess of each event < 30 day away for each city
                for event in database_events(ticket, evb):

                    # Put all attendees in the db and return those who answered the survey
                    attendees = database_attendees( evb, event )
                    while True:
                        try:
                            attendee, interests  = attendees.next()
                        except StopIteration:
                            break

                        # For each interest match sponsers
                        for interest in interests:

                            # Return a sponser list and a normalized interest
                            deals = event.get_deals( interest = interest )
                            for deal in deals:
                                if event.add_connection( attendee, deal ):
                                    make_contact( event,
                                                  interest,
                                                  deal,
                                                  attendee,
                                                  template
                                            )

if __name__ == '__main__':
    main()
