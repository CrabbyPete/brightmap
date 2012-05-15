import django_header
import settings

# Python libraries
from datetime                       import  datetime, timedelta
from termcolor                      import  colored

# Django libraries
from django.contrib.auth.models     import  User
from django.core.urlresolvers       import  reverse


# Local libraries
from nameparser                     import  HumanName
from eventapi                       import  EventBrite
from base.models                    import ( Event, Profile, Survey, Interest, Deal, 
                                             Organization, Connection, LeadBuyer, Invite
                                            )

from social.models                  import AuthToken

from mail                           import  Mail
Mail = Mail()
 
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

def mail_buyer ( user, invite ):
    """ 
    Send email to potential leadbuyer asking them to join 
    """
    if PROMPT:
        ans = raw_input('Send Leadbuyer request? (y/n)')
        if ans != 'y':
            return
    
    sender   = invite.chapter.organizer.email
    receivers = [ user.email ]
    subject  = 'Become a preferred provider for '+ invite.chapter.name
    url      = reverse('or_landing')+'?invite='+ str(invite.pk)

    Mail.message( sender        = sender, 
                 receivers     = receivers,
                 subject       = subject,
                 template_name = 'leadbuyer.tmpl',
                 bcc           = [sender], 
                 user          = user, 
                 url           = url,  
                 chapter       = invite.chapter
               )
    
 
def attendee_user( attendee ):
    """
    Return a user record for the attendee, if non exists create a new one
    """
    # Check if they are a user
    try:
        user = User.objects.get( email = attendee['email'] )

    # If not create a new user
    except User.DoesNotExist:

        # Create a temporary password and username which is 30 chars max
        password = 'pamthgirb'   # brightmap backwards
        username = attendee['email'][0:30]
        try:
            user = User.objects.create_user(  username = username,
                                              email    = attendee['email'],
                                              password = password
                                            )
        except Exception, error:
            message = "Exception creating user:" + str(error)
            print message
            logger.error( message )
            return None
            
            
        name = attendee['first_name'].strip()+ ' '+ attendee['last_name'].rstrip()
        try:
            name = HumanName(name)
            name.capitalize()
        except:
            user.first_name = attendee['first_name'].strip().capitalize()
            user.last_name  = attendee['last_name'].rstrip().capitalize()
        else:
            user.first_name = name.first.capitalize()
            user.last_name  = name.last.capitalize()
            
            user.save()
            profile = Profile( user = user )
            profile.save()
        
    except KeyError:
        if 'email' in attendee:
            print log("No email address for:%s"%(attendee['email'],))
        else:
            print log("No Attendee information recieved",'red')
            return None
 
    return user


def database_attendees( event, api ):
    """
    Generator to put the attendees in the database, returns attendees who
    answered the survey
    """

    # Get all the attendees for the event from Eventbrite
    attendees = api.get_attendees( event.event_id )

    # Add all attendees to the database
    for attendee in attendees:

        user = attendee_user( attendee )
        if not user:
            continue

        try:
            profile = user.get_profile()
        except:
            continue

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
        if leadbuyer and not profile.is_leadbuyer:
            try:
                invite = Invite.objects.get( user = user, chapter = event.chapter )
            except Invite.DoesNotExist:
                invite = Invite( user = user, 
                                 chapter = event.chapter
                               )
                invite.sent = 1
                invite.save() 
                
                mail_buyer( user, invite )
                profile.is_leadbuyer = True
                profile.save()
            
        # Add the attendee with or with out interests to the event
        if len(interests) == 0:
            query = Survey.objects.filter( event = event,
                                           attendee = user
                                         )
            if len(query) == 0:
                #print user.first_name + ' ' + user.last_name
                
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
            if '(' in interest:
                interest = interest.split('(')[0]
            
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
        #print "Yield " + user.first_name + ' ' + user.last_name
        yield surveys

    #print "Return"


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


def filter_company( company ):
    """
    Filter out non company titles
    """
    if not company:
        return company
    
    # Normalize the company name and see if its a company name
    normalize = company.lower().strip()
    if normalize in ['freelancer', 'na', 'n/a', 'self', '']:
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
    active = deal.active()
    for term in active:
        
        #print "Term " + str( term.pk )+ " Active "+ str( len(active) )
        # During test sometimes None would be set to a term, make sure term exists
        if term == None:
            continue
        
        # If you had a good deal that went bad .eg trial expires notify user
        if not term.execute( event = survey.event ):
            continue
             
        # Don't spam, limit the number of emails per event, per interest
        if survey.mails_for() > MAX_MAIL_SEND:
            continue
           
        # Determine if the budget is exceeded, don't send the connection
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
        
        # If the prompt was set ask before sending
        if PROMPT:
            ans = raw_input('Send Connection? (y/n)')
            if ans != 'y':
                continue
        
        
        subject = deal.chapter.organization.name + ' Intro: '+ interest.interest + ' for ' + attendee.first_name + ' ' + attendee.last_name
        recipients = [ '%s %s <%s>'% ( attendee.first_name, attendee.last_name, attendee.email ),
                       '%s %s <%s>'% ( sponser.first_name, sponser.last_name, sponser.email )
                     ]

        sender =  '%s %s <%s>' % ( organizer.first_name, organizer.last_name, organizer.email )    
        Mail.message( sender, recipients, subject, letter, bcc = [sender],
                      interest   = interest,
                      attendee   = attendee,
                      sponser    = sponser,
                      organizer  = organizer,
                      chapter    = chapter,
                      event      = event,
                      company    = company
                    ) 
                      
def print_event(event):
    """
    Print Event details
    """
    delta = event.date - datetime.today()
    date  = event.date.strftime("%Y-%m-%d %H:%M")
    try:
        print log('Chapter: '+ event.chapter.name  + ' Event: ' +  event.describe + ' ' + date + ' ' + str(delta.days) )
    except:
        #logger.error( "Error printing event %s",event.chapter.name )
        pass
    
def print_connection( attendee, sponser, interest ):
    """
    Print Connection details
    """
    try:
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
    except:
        #logger.error( "Error printing connection")
        pass


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
            else:
                letter = letter.name

            # Get the attendess of each event
            events = database_events( ticket, api )
            if len(events) == 0:
                print log("Chapter:" + chapter.name +' has no events')
                continue
            
            for event in events:

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
                    try:
                        print log( "%s:%s  has no surveys"%(chapter.name, event.describe),'green')
                    except:
                        pass


#import cProfile        
import optparse
if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    # Add options for debugging
    op.add_option('-d', action="store_true", help = 'Turn off debug email messages')
    op.add_option('-p', action="store_true", help = 'Prompt to send')
    op.add_option('-a', action="store_true", help = 'Do not run accounting')
    op.add_option('-e', action="store_true", help = 'Do not check for trial deal')

    opts, args = op.parse_args()

    # Check if options were set
    if opts.d:
        TEST_EMAIL = True
    else:
        TEST_EMAIL = False

    if opts.p:
        PROMPT = True
    else:
        PROMPT = False
    
    # Got and check for new events
    #cProfile.run('main()')
    main()
    
    
 
