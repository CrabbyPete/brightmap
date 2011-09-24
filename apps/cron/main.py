import django_header

# Python libraries
from datetime                       import datetime, date

# Django libraries
from django.contrib.auth.models     import User
from django.template                import loader, Context
from django.core.mail               import send_mail,\
                                           EmailMessage,EmailMultiAlternatives
# Local libraries
from base.models                    import *
from base.passw                     import gen
from client                         import EventbriteClient
from meetup                         import MeetUpAPI
from social.models                  import MeetupProfile

import logging
logger = logging.getLogger('main.py')


# Environment variables
from settings                       import EVENTBRITE, MAX_MAIL_SEND, SEND_EMAIL
PROMPT     = False

def log(message):
    """
    Time stamp all messages
    """
    return datetime.today().strftime("%Y-%m-%d %H:%M")+ ',' + message


def get_attendees( evb, event_id ):
    """
    Get all the attendees for an event from Eventbrite
    """
    attendee_list = []

    # Get all the attendees of each event (New York, Boston, Toronto ..)
    try:
        attendees = evb.list_event_attendees( event_id = int(event_id) )
    except:
        print log('Eventbrite Error: No attendees for event id ' + str(event_id) )
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


def get_latest_events( evb, organizer_id ):
    """
    Search for the latest events
    """
    try:
        events = evb.list_organizer_events(organizer_id = organizer_id)
    except:
        print log( 'Eventbrite Error: Events for ' + organizer_id )
        logger.debug('Eventbrite Error: Events for ' + organizer_id )
        return []

    # Check if you get an error from Eventbrite
    if 'error' in events:
        err = 'Eventbrite Error: ' + events['error']['error_type'] + ' for ' + str(organizer_id)
        print log( err )
        #logger.debug( err )
        return []

    # Compare to todays date and find all events ending after today
    today = datetime.today()

    # Look through all events and keep all future events
    event_ids = []
    for event in events['events']:

        # Make sure these are not past events
        end_date = datetime.strptime(event['event']['end_date'],
                                     "%Y-%m-%d %H:%M:%S")
        # Only get future events
        if end_date < today:
            continue

        event_ids.append([ event['event']['title'],
                           event['event']['id'],
                           end_date
                          ]
                         )
    return event_ids


def database_events(organizer, evb = None):
    """
    Put the latest event in the database
    """
    if evb == None:

        # Open a new Eventbrite client
        evb = EventbriteClient( app_key  = EVENTBRITE['APP_KEY' ],
                                user_key = organizer.user_key     )

    # Get the latest from Eventbrite
    events = get_latest_events(evb, int(organizer.organizer_id) )
    event_list = []

    # Add each event and find the right organizer
    for event in events:
        try:
            event_rec = Event.objects.get(event_id = event[1])
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

def database_attendees( evb, event ):
    """
    Generator to put the attendees in the database, returns attendees who
    answered the survey
    """

    # Get all the attendees for the event from Eventbrite
    attendees = get_attendees( evb, event.event_id )

    # Add all attendees to the database
    for attendee in attendees:

        # Check if they are a user
        try:
            user = User.objects.get( email = attendee['email'] )

        # If not create a new user
        except User.DoesNotExist:

            # Create a temporary password and username which is 30 chars max
            password = gen()
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
                """ If you want to automatically save interests
                normal_interest = Interest( interest = interest )
                normal_intest.save()
                else:
                """
                continue

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


def make_contact( survey, deal, template ):
    """
    Send an email to those attendees who answered the survey and have a
    corresponding lead buyer for an interest
    """
    if deal == None:
        return

    for term in deal.terms():
        # Determine whether to execute this deal
        if term == None or not term.execute( event = survey.event ):
            continue

        # Don't spam, limit the number of emails per event
        if survey.mails_for() > MAX_MAIL_SEND:
            continue

        # Determine if you did this or not
        if not survey.event.add_connection( survey, term ):
            continue

        # Count email so you don't spam
        survey.mailed += 1
        survey.save()

        # Set up the email template
        sponser      = term.buyer
        attendee     = survey.attendee
        event        = survey.event
        interest     = deal.interest
        organizer    = survey.event.chapter.organizer
        chapter      = event.chapter.name

        c = Context({'interest'    :interest,
                     'attendee'    :attendee,
                     'sponser'     :sponser,
                     'organizer'   :organizer,
                     'chapter'     :chapter
                     })

        # Render the message and log it
        message = template.render(c)
        print_connection( attendee, sponser, interest )

        subject = deal.chapter.organization.name + ' Intro: '+ interest.interest

        recipients = [ '%s %s <%s>'% ( attendee.first_name, attendee.last_name, attendee.email ),
                       '%s %s <%s>'% ( sponser.first_name, sponser.last_name, sponser.email )
                     ]

        bcc = [ 'bcc@brightmap.com',
                event.chapter.organizer.email
              ]

        #TESTING BELOW REMOVE LATER
        #recipients = ['Pete Douma <pete.douma@gmail.com>']

        # Send the email
        msg = EmailMultiAlternatives( subject,
                                      message,
                                      '%s %s <%s>' % ( organizer.first_name,
                                                       organizer.last_name,
                                                       organizer.email       ),
                                      recipients,
                                      bcc
                                     )

        # If the prompt was set ask before sending
        if PROMPT:
            ans = raw_input('Send? (y/n)')
            if ans != 'y':
                continue

        # Try and send the message
        log_mess = "%s,%s,%s,%s"%( attendee.email,
                                   sponser.email,
                                   chapter,
                                   interest
                                 )

        logger.info(log(log_mess))
        if SEND_EMAIL:
            try:
                msg.send( fail_silently = False )
            except:
                err = "Email Send Error For:"+log_mess
                print log(err)
                #logger.error(log(err))


def print_event(event):
    """
    Print Event details
    """
    delta = event.date - datetime.today()
    print log('Event - ' +  event.describe + ' ' + str(delta.days) )


def print_connection( attendee, sponser, interest ):
    """
    Print Connection details
    """
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

def main():
    # Get all organizers
    organizations = Organization.objects.all()
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
                app_key  = EVENTBRITE['APP_KEY' ]
                user_key = ticket.user_key
                evb = EventbriteClient( app_key = app_key, user_key = user_key )

                #Get the email template for this organization
                letter = chapter.letter
                if letter != None:
                    template = loader.get_template(letter.letter)
                else:
                    template = loader.get_template( 'letters/default.tmpl' )

                # Get the attendess of each event
                for event in database_events( ticket, evb ):

                    # Log the events
                    print_event(event)

                    # Put all attendees in the db and return surveys
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
                            else:
                                if deal == None:
                                    print log( chapter.name +        \
                                           ' has no deal for ' + \
                                           survey.interest.interest
                                          )
                                    continue

                            # Connect attendees and mail contacts
                            make_contact( survey, deal, template )

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