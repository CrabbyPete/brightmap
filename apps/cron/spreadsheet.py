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
from google                         import GoogleSpreadSheet

def spreadsheet( email, password ):

   # Open Google Docs and get the spreadsheet
    spreadsheet = GoogleSpreadSheet( email, password )
    result = spreadsheet.getSpreadSheet(settings.SPREADSHEET)
    if result == None or result.title.text != settings.SPREADSHEET:
        print "Google Spreadsheet Error, Found: "  + result.title.text + \
              " Looking for: " + settings.SPREADSHEET
        return None

    # Open the Organizers worksheet
    spreadsheet.getWorkSheet('Organization')
    organizations = spreadsheet.getCells()

    # Put all organizers in the database
    for organization in organizations:

        # Make sure all the necessary keys are present
        try:
            name      = organization['Organization']
            chapter   = organization['Chapter']
            email     = organization['Organizer Email']
            organizer = organization['Chapter Organizer']
            user_key  = organization['API User Key']
            org_id    = organization['Organizer ID']

        except KeyError, e:
            print "Key Error: " + e.message
            continue

        # Get the organization or create one
        try:
            d_organization = Organization.objects.get( name = name )
            state = 'Exists:'
        except Organization.DoesNotExist:
            d_organization = Organization( name = name )
            d_organization.save()
            state = 'Create:'
            
        print state + \
              name      + ' ' +\
              chapter   + ' ' +\
              email     + ' ' +\
              organizer + ' ' +\
              user_key  + ' ' +\
              org_id  

        # Get the organizer or create one
        try:
            user = User.objects.get( email = email )
            profile = user.get_profile()

        except User.DoesNotExist:

            # Create a temporary password and username which is 30 chars max
            first,last = organizer.split()
            password = first + '$' + last
            username = email[0:30]
            user = User.objects.create_user(  username = username,
                                              email    = email,
                                              password = password
                                            )
            user.first_name = first.capitalize()
            user.last_name  = last.capitalize()
            user.save()
            profile = Profile( user = user )
            profile.is_organizer = True
            profile.save()

        # Get the chapter or create one
        try:
            d_chapter = Chapter.objects.get( name = chapter )
            d_chapter.organizer = user

        except Chapter.DoesNotExist:
            d_chapter = Chapter( name = chapter,
                                 organization = d_organization,
                                 organizer = user
                               )
        d_chapter.save()


        # Get the eventbrite access
        try:
            ticket = Eventbrite.objects.get( user_key     = user_key,
                                             organizer_id = org_id
                                           )
        except Eventbrite.DoesNotExist:
            ticket = Eventbrite( user_key = user_key,
                                 organizer_id = org_id
                                )

        # Set the current chapter
        ticket.chapter = d_chapter
        ticket.save()

        # Get all the sponsers for the current chapter
        result = spreadsheet.getWorkSheet(chapter)

        # Check to make sure there is a corresponding worksheet with sponsors
        if result == None:
            print 'No Work Sheet for: '+ chapter
            continue

        sponsers = spreadsheet.getCells()
        for sponser in sponsers:

            # Check to make sure all fields exist
            try:
                email   = sponser['Sponsor Email']
                first   = sponser['Sponsor First Name']
                last    = sponser['Sponsor Last Name']
            except KeyError, err:
                print "Key Error: " + err.message
                continue
            
            if 'Sponsor Company' in sponser:
                company = sponser['Sponsor Company']
            else:
                company = None
            if 'Sponsor Title' in sponser:
                title = sponser['Sponsor Title']
            else:
                title = None
            if 'Sponsor Website' in sponser:
                website = sponser['Sponsor Website']
            else:
                website = None
 
            # Get or create the user
            try:
                user = User.objects.get(email = email)
                profile = user.get_profile()

            except User.DoesNotExist:
                password = first+'$'+last,
                username = email[0:30]
                user = User.objects.create_user(  username = username,
                                                  email    = email,
                                                  password = password
                                                )
                user.first_name = first.capitalize()
                user.last_name  = last.capitalize()
                user.save()
                profile = Profile( user = user )
                profile.save()

            profile.company = company
            profile.title   = title
            profile.website = website
            profile.is_leadbuyer = True
            profile.save()

            # Get or create a lead buyer for this user
            try:
                lb = LeadBuyer.objects.get(user = user)
            except LeadBuyer.DoesNotExist:
                lb = LeadBuyer(user = user)
                lb.save()

            # Any key that does not start with Sponsor is an interest
            keys = sponser.keys()
            
            # Default deal is good til cancel
            deal_term = "cancel: ,20"
            for key in keys:

                # Check optional sponsor details
                if 'Sponsor' in key:
                    if key == 'Sponsor Deal':
                        deal_term = sponser['Sponsor Deal']
                    continue

                # Get or create an interest, make sure their is an 'x' in the box
                if sponser[key] != 'x':
                    continue
                
                try:
                    interest = Interest.objects.get(interest = key)
                except Interest.DoesNotExist:
                    key = key.lstrip().rstrip()
                    interest = Interest( interest = key )
                    interest.save()

                 # Get or create a deal
                try:
                    deal = Deal.objects.get( chapter = d_chapter,
                                             interest = interest
                                            )
                except Deal.DoesNotExist:
                    deal = Deal( chapter = d_chapter,
                                 interest = interest,
                                )
                    deal.save()

                # Get or create a term
                term_type, cost = deal_term.split(',')
                term_type = term_type.split(':')
                try:
                    term = Term.objects.get( deal = deal, buyer = user )
                except Term.DoesNotExist:
                    # Good til Canceled
                    if 'cancel'    == term_type[0] or \
                       'sponsored' == term_type[0] or \
                       'exclusive' == term_type[0]     :
                        try:
                            number = int(term_type[1])
                        except ValueError:
                            number = 0
                        
                        lb.budget = number
                        lb.save()
                    
                        if number != 0:
                            term = Budget ( deal = deal, 
                                            buyer = user,
                                            cost = cost,
                                            remaining = number,
                                            status = 'approved'
                                          )
                        else:
                            term = Cancel( deal   = deal,
                                           buyer  = user,
                                           cost   = cost,
                                           status = 'approved'
                                         )
                        
                        if 'exclusive' == term_type[0]:
                            term.exclusive = True
                        
                        term.save()
                    # Good til exires
                    elif 'expire' == term_type[0]:
                        date = datetime.strptime(term_type[1],"%m/%d/%y")
                        term = Expire( deal   = deal,
                                       buyer  = user,
                                       cost   = 0,
                                       date   = date,
                                       status = 'approved'
                                     )

                    # Good for x number of events
                    elif 'count'  == term_type[0]:
                        try:
                            number = int(term_type[1])
                        except ValueError:
                            number = 0
                    
                        term = Count( deal      = deal,
                                      buyer     = user,
                                      cost      = cost,
                                      number    = number,
                                      remaining = number,
                                     )

                    # Good for x number of connections
                    elif 'connects' == term_type[0]:
                        try:
                            number = int(term_type[1])
                        except ValueError:
                            number = 0
                        
                        term = Connects( deal      = deal,
                                         buyer     = user,
                                         cost      = cost,
                                         number    = number,
                                         remaining = number
                                        )
                    else:
                        print "Error No Deal Type: ", + term_type[1]

                    term.save()
                
                # Update an existing deal
                else:
                    # Determine child type
                    cterm = term.get_child()
                    # This should never be None, unless a term bombed while save
                    if cterm != None:
                        cterm.cost = cost
                        if isinstance(cterm,Expire):
                            cterm.date = datetime.strptime( term_type[1],
                                                            "%m/%d/%y"
                                                          )
                        elif isinstance(cterm,Count) or \
                             isinstance(cterm,Connects):
                            try:
                                number = int(term_type[1])
                            except ValueError:
                                pass
                            else:
                                cterm.number    = int(term_type[1])
                                cterm.remaining = int(term_type[1])
                                cterm.save()
                    else:
                        print "No Terms for : "+ term

import cProfile
if __name__ == '__main__':

    import optparse
    op = optparse.OptionParser( usage="usage: %prog " +
                                "<Google User> <Google Password>" )

    opts,args = op.parse_args()

    if len(args) >=2:
        email    = args[0]
        password = args[1]

    # Pass in gmail address and password
    #cProfile.run( 'spreadsheet(email, password)' )
    spreadsheet(email, password)
