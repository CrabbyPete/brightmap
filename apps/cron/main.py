import django_header


# Python libraries
from datetime                       import  datetime, timedelta
from termcolor                      import  colored

# Django libraries
from django.contrib.auth.models     import  User
from django.core.urlresolvers       import  reverse

# Local libraries
from eventapi                       import  EventBrite
from base.models                    import ( Event, Profile, Survey, Interest, Deal, Expire,
                                             Organization, Connection, LeadBuyer, Invoice    )

from base.mail                      import  Mail 
from base.passw                     import  gen


import logging
logger = logging.getLogger('main.py')


# Environment variables
from settings                       import EVENTBRITE, MAX_MAIL_SEND

PROMPT     = False
TEST_EMAIL = False

TODAY      = datetime.today()


def log(message, color = None):
    """
    Time stamp all messages
    """
    string = TODAY.strftime("%Y-%m-%d %H:%M")+ ',  ' + message
    if color:
        string = colored(string, color )
        
    return string


def database_events( organizer, api ):
    """
    Put the latest event in the database
    """
 
    # Get the latest from Eventbrite
    if not organizer.organizer_id:
        return []
    
    events = api.get_latest_events( int(organizer.organizer_id) )
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
        else:
            # Update any changes to the date or description
            event_rec.describe = event[0]
            event_rec.date     = event[2]
        
        
        event_rec.save()
            
        event_list.append(event_rec)

    # Return the events list
    return event_list

def mail_buyer ( user, event ):
    """ 
    Send email to potential leadbuyer asking them to join 
    """
    sender   = ['request@brightmap.com']
    receiver = [ user.email]
    bcc      = None,
    subject  = 'Brightmap Invitation'
    url      = reverse('lb_signup')
    
    mail = Mail( sender, receiver,subject,'leadbuyer.tmpl',bcc, 
                 user = user, 
                 url = url,  
                 chapter = event.chapter
               )
    mail.send()


def database_attendees( event, api ):
    """
    Generator to put the attendees in the database, returns attendees who
    answered the survey
    """

    # Get all the attendees for the event from Eventbrite
    attendees = api.get_attendees( event.event_id )

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
            user.first_name = attendee['first_name'].strip().capitalize()
            user.last_name  = attendee['last_name'].rstrip().capitalize()
            user.save()
            profile = Profile( user = user )
        
        except KeyError:
            if 'email' in attendee:
                print log("No email address for:%s %s"%(attendee['email'],))
            else:
                print log("No Attendee information recieved",'red')
            continue
        
        else:
            profile = user.get_profile()

        # Update any profile changes
        profile.is_attendee = True

        # Don't change the company name if the person is a leadbuyer
        if 'company' in attendee and not profile.is_leadbuyer:
            profile.company = attendee['company'].rstrip()
        
        if 'cell_phone' in attendee:
            profile.phone = attendee['cell_phone'].rstrip()
        profile.save()

        # Return attendees who answered the survey
        interests, leadbuyer = api.check_survey( attendee )

        # If they checked they want leads they are a leadbuyer
        if leadbuyer:
            mail_buyer( user, event )
            
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


def days_of_month (month = None):
    """
    Return the first and last day of the month
    """
    first_day = TODAY.replace(day = 1)
    if  month:
        first_day = first_day.replace( month = int(month) )
 
    if first_day.month == 12:
        last_day = first_day.replace ( day = 31 )
    else:
        last_day = first_day.replace (month = first_day.month + 1 ) - timedelta( days = 1 )
    
    return (first_day, last_day)



def check_budget( term ):
    """
    Check if the LeadBuy has gone over budget
    """
    leadbuyer = LeadBuyer.objects.get( user = term.buyer )
    if not leadbuyer.budget:
        return True
           
    connections = Connection.objects.for_buyer( term.buyer, days_of_month() )
    total = sum( connection.term.cost for connection in connections if connection.status == 'sent' )
 
    if total >= leadbuyer.budget:
        return False
  
    return True


def warn_user( term ):
    child = term.get_child()
    if isinstance(child, Expire):
        buyer     = term.buyer
        organizer = term.deal.chapter.organizer
 
        mail = Mail( [organizer.email],
                     [buyer.email], 
                     'Trial Deal Expiration',
                     'expire_notice.tmpl',
                     buyer = buyer,
                     term  = term,
                     url   = reverse('lb_dash')
                    )
        mail.send()
        return
 
def make_contact( survey, deal, letter ):
    """
    Send an email to those attendees who answered the survey and have a
    corresponding lead buyer for an interest
    """
    if deal == None:
        return

    # Go through all the active deals
    for term in deal.active():
        
        # During test sometimes None would be set to a term, make sure term exists
        if term == None:
            continue
        
        # If you had a good deal that went bad .eg trail expires notify user
        if not term.execute( event = survey.event ):
            warn_user( term )
            continue
             
        # Don't spam, limit the number of emails per event
        if survey.mails_for() > MAX_MAIL_SEND:
            continue
   
        # Determine if the budget is exceeded
        if not check_budget( term ):
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
        chapter      = event.chapter
        
        # Check if they put in a company or junk
        company      = attendee.get_profile().company
        if company and company.lower() in ['freelancer','na','n/a','self','']:
            company = None
        
        # Check if the leadbuyer is the organizer and if they have a letter
        if sponser == organizer:
            letter = 'self_referral.tmpl'

  
        # Render the message and log it
        print_connection( attendee, sponser, interest )
        subject = deal.chapter.organization.name + ' Intro: '+ interest.interest
        recipients = [ '%s %s <%s>'% ( attendee.first_name, attendee.last_name, attendee.email ),
                       '%s %s <%s>'% ( sponser.first_name, sponser.last_name, sponser.email )
                     ]

        senders =    ['%s %s <%s>' % ( organizer.first_name, organizer.last_name, organizer.email )]     
        mail  = Mail( senders, recipients, subject, letter, bcc = senders,
                      interest   = interest,
                      attendee   = attendee,
                      sponser    = sponser,
                      organizer  = organizer,
                      chapter    = chapter,
                      event      = event,
                      company    = company
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
        mail.send()
                


def print_event(event):
    """
    Print Event details
    """
    delta = event.date - datetime.today()
    date  = event.date.strftime("%Y-%m-%d %H:%M")
    print log('Chapter: '+ event.chapter.name  + ' Event: ' +  event.describe + ' ' + date + ' ' + str(delta.days) )


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
                api = EventBrite( tokens = app_key, user_key = user_key )
        
                #Get the email template for this organization
                letter = chapter.letter
                if not letter:
                    letter = 'default.tmpl'

                # Get the attendess of each event
                for event in database_events( ticket, api ):

                    # Log the events
                    print_event(event)

                    # Put all attendees in the db and return surveys
                    for surveys in database_attendees( event, api ):

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
                                    print log( chapter.name +    \
                                               ' has no deal for ' + \
                                               survey.interest.interest,
                                               'red'
                                             )
                                    continue

                            # Connect attendees and mail contacts
                            make_contact( survey, deal, letter )
                            
                    leads = event.surveys(True)
                    if len( leads ) == 0:
                        print log( "%s:%s  has no surveys"%(chapter.name, event.describe),'green')


def accounting():
    """
    Update all the invoices for the month
    """
    print "Invoicing for the month of: " + TODAY.strftime("%B %Y")
    for profile in Profile.objects.filter( is_leadbuyer = True ):
        
        days = days_of_month()
        user = profile.user
        
        connections = Connection.objects.for_buyer( user, days )
        cost = sum( connection.term.cost for connection in connections if connection.status == 'sent' )
 
        if not cost:
            continue
 
        title = days[0].strftime("%B %Y")
                
        # See if there is an existing invoice for this month
        try:
            invoice = Invoice.objects.get( user      = user,
                                           title     = title,
                                           first_day = days[0],
                                           last_day  = days[1]  )
        except Invoice.DoesNotExist:
            # Create an invoice 
            invoice = Invoice( user      = user, 
                               title     = title,
                               first_day = days[0], 
                               last_day  = days[1] 
                             )
    
        invoice.cost = cost
        invoice.status = 'pending'
        invoice.save()
        print profile.user.first_name + ' ' + profile.user.last_name + " = " + str( invoice.cost )

import optparse
if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    # Add options for debugging
    op.add_option('-d', action="store_true", help = 'Turn off debug email messages')
    op.add_option('-p', action="store_true", help = 'Prompt to send')
    op.add_option('-a', action="store_true", help = 'Run Accounting')

    opts,args = op.parse_args()

    # Check if options were set
    if opts.d:
        TEST_EMAIL = True
    else:
        TEST_EMAIL = False

    if opts.p:
        PROMPT = True
    else:
        PROMPT = False
    
    main()
    accounting()