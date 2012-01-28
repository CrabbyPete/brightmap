import django_header


# Python libraries
from datetime                       import  datetime, timedelta, date
from termcolor                      import  colored

# Django libraries
from django.contrib.auth.models     import  User
from django.core.urlresolvers       import  reverse

# Local libraries
from eventapi                       import  EventBrite
from base.models                    import ( Event, Profile, Survey, Interest, Deal, Expire,
                                             Organization, Connection, LeadBuyer, Invoice,
                                             Cancel
                                            )

from social.models                  import AuthToken

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


def database_events( ticket, api ):
    """
    Put the latest event in the database
    """
    if 'organizer_id' in ticket:
        organizer_ids = [ ticket['organizer_id'] ]
    else:
        organizer_ids = api.get_organizers()
    
    event_list = []
    for organizer_id in organizer_ids:
        if not organizer_id:
            continue
        events = api.get_latest_events( int(organizer_id) )
   
        # Add each event and find the right organizer
        for event in events:
            try:
                event_rec = Event.objects.get(event_id = event[1])
            except Event.DoesNotExist:
                event_rec = Event( event_id        = event[1],
                                   describe        = event[0],
                                   date            = event[2],
                                   chapter         = ticket['chapter']
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
    sender   = 'request@brightmap.com'
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
    
    warning_level = float(leadbuyer.budget) * 0.80
    if total >= warning_level:
        buyer     = term.buyer
        organizer = term.deal.chapter.organizer
 
        mail = Mail( organizer.email,
                     [buyer.email], 
                     'Budget',
                     'budget_notice.tmpl',
                     buyer = buyer,
                     budget = leadbuyer.budget,
                     total = total,
                     url   = reverse('lb_dash')
                    )
        mail.send()
    
    
    return True


def warn_user( term, warning = False ):
    """
    Warn a deal buyer that their deal has changed, if warning is about to expire
    """
    child = term.get_child()
    if isinstance(child, Expire) or isinstance(term, Expire):
        buyer     = term.buyer
        organizer = term.deal.chapter.organizer
        if warning:
            template = 'expire_notice.tmpl'
        else:
            template = 'expire_warning.tmpl'
            
        mail = Mail( organizer.email,
                     [buyer.email],
                     'Trial Deal Expiration',
                     template,
                     bcc = [organizer.email], 
                     buyer = buyer,
                     term  = term,
                     url   = reverse('lb_dash')
                    )
        
        if not mail.send():
            print log('Error sending email to %s for deal expiration'%( buyer.email,))
        
        # If this is not warning create a new paid deal
        if not warning:
            new_term = Cancel(  deal  = term.deal,
                                cost  = 20,
                                buyer = term.buyer,
                                exclusive = False,
                                status = 'approved'
                             )
            new_term.save()
        
    return
 
def filter_company( company ):
    """
    Filter out non company titles
    """
    if not company:
        return company
    c = company.lower().strip()
    if c in ['freelancer','na','n/a','self','']:
        return None
    return company
 

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
        
        # If you had a good deal that went bad .eg trial expires notify user
        if not term.execute( event = survey.event ):
            warn_user( term ) # This should never be hit now we do it up front. 
            continue
             
        # Don't spam, limit the number of emails per event
        if survey.mails_for() > MAX_MAIL_SEND:
            continue
   
        # Determine if the budget is exceeded
        if not check_budget( term ):
            continue
        
        
        # Determine if you did this or not
        connection = survey.event.add_connection( survey, term )
        if not connection:
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
        company      = filter_company(company)
  
        # Check if the leadbuyer is the organizer and if they have a letter
        if sponser == organizer:
            letter = 'self_referral.tmpl'

  
        # Render the message and log it
        print_connection( attendee, sponser, interest )
        subject = deal.chapter.organization.name + ' Intro: '+ interest.interest
        recipients = [ '%s %s <%s>'% ( attendee.first_name, attendee.last_name, attendee.email ),
                       '%s %s <%s>'% ( sponser.first_name, sponser.last_name, sponser.email )
                     ]

        sender =  '%s %s <%s>' % ( organizer.first_name, organizer.last_name, organizer.email )    
        mail  = Mail( sender, recipients, subject, letter, bcc = [sender],
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
        if not mail.send():
            print log( "Error sending mail for %s"%(sender,) )
                


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


def get_ticket(chapter):
    """
    Get access to Eventbrite API
    """
    ticket = {'chapter':chapter}
    # First check for AuthTokens
    try:
        # Returns user, service,token,refresh,created
        eventbrite = AuthToken.objects.get(user = chapter.organizer, service = 'eventbrite')
        ticket.update( {'access_code':eventbrite.token} )
    except AuthToken.DoesNotExist:
        # Returns chapter,  user_key, organizer_id, bot_email
        eventbrite = chapter.get_eventbrite()
        if eventbrite:
            if eventbrite.organizer_id:
                ticket.update( {'organizer_id':eventbrite.organizer_id} )
            
            if eventbrite.user_key:
                ticket.update( {'user_key':eventbrite.user_key} )
    
    return ticket
           
    
def main():
    # Get all organizers
    organizations = Organization.objects.all()
    for organization in organizations:
        for chapter in organization.chapter_set.all():

            # Open a new Eventbrite client
            ticket = get_ticket(chapter)
            if 'access_code' in ticket:
                api = EventBrite( access_token = ticket['access_code'] )
            elif 'user_key' in ticket:
                app_key  = EVENTBRITE['APP_KEY' ]
                api = EventBrite( app_key = app_key, user_key = ticket['user_key'] )
            else:
                print log("No configuration data for " + chapter.name )
                continue

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
                            print log( chapter.name + ' has no deal for ' + survey.interest.interest )
                            continue
                        
                        if deal == None:
                            print log( chapter.name + ' has no deal for ' + survey.interest.interest,
                                       'red'
                                     )
                            continue

                        # Connect attendees and mail contacts
                        make_contact( survey, deal, letter )
                            
                # Check if any active surveys
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



def check_expired():
    expires = Expire.objects.filter(status='approved')
    for expire in expires:
        day =  date.today()
        warning_day = day - timedelta( days = 5 )
        if expire.date < date.today():
            print log( 'Converting trial deal for '+\
                       expire.buyer.last_name+','+expire.buyer.first_name+ ' ' +\
                       expire.date.strftime("%Y-%m-%d") + ' '+\
                       expire.deal.chapter.name +\
                       ' with ' + str( len(expire.connections()) )+ ' connections: '
                     )

            #expire.canceled()
            #warn_user(expire)
        
        # Warn the user 5 days before. Make sure main is only run once a day.
        elif expire.date == warning_day:
            print str( expire.pk ) + ' ' + expire.buyer.last_name +' ' + expire.date.strftime("%Y-%m-%d %H:%M")
            warn_user( expire, warning = True )
            
import optparse
if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    # Add options for debugging
    op.add_option('-d', action="store_true", help = 'Turn off debug email messages')
    op.add_option('-p', action="store_true", help = 'Prompt to send')
    op.add_option('-a', action="store_true", help = 'Do not run accounting')
    op.add_option('-e', action="store_true", help = 'Do not check for trial deal')

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
    
    # Check for trial deals that are expiring
    if not opts.e:
        check_expired()
    
    # Got and check for new events
    main()
    
    # Check billing
    if not opts.a:
        accounting()
    
