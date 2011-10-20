import django_header

# Python libraries
from datetime                       import datetime

# Django libraries
from django.contrib.auth.models     import User
from django.template                import loader, Context
from django.core.mail               import send_mail,EmailMessage, \
                                           EmailMultiAlternatives
# Local libraries
from base.models                    import *
from client                         import EventbriteClient
from google                         import GoogleSpreadSheet
from settings                       import SPREADSHEET, EVENTBRITE



valid_deals = ('cancel','sponsored','exclusive','expire')

def update_term( term, term_type, cost ):
    """
    Check if changes required for an existing term
    """
    # Determine child type
    cterm = term.get_child()

    # This should never be None, unless a term bombed while save
    if cterm == None:
        return None
    
    cterm.cost = cost
    if isinstance(cterm,Expire):
        # If this is a new type you have to change the old deal
        if term_type[0] != 'Trial':
            term.canceled()
            term.save()
            
            deal = term.deal
            term = new_term(term.deal, term.buyer, term_type, cost )
            return term
        else: 
            cterm.date = datetime.strptime( term_type[1], "%m/%d/%y" )

    elif isinstance(cterm,Count) or \
         isinstance(cterm,Connects):
        try:
            number = int(term_type[1])
        except ValueError:
            pass
        else:
            cterm.number    = int(term_type[1])
            cterm.remaining = int(term_type[1])

    elif isinstance(cterm,Budget):
        try:
            number = int(term_type[1])
        except ValueError:
            pass
        else:
            cterm.remaining = number
    cterm.save()
    return cterm


def new_term( deal, user, term_type, cost ):
    """
    Create a new term
    term_type eg. 'cancel,500,20'
    """
    # Good til Canceled
    if 'cancel'    == term_type[0] or \
       'sponsored' == term_type[0] or \
       'exclusive' == term_type[0]     :
        try:
            number = int(term_type[1])
        except ValueError:
            number = 0

        if number != 0:
            term = Budget ( deal      = deal,
                            buyer     = user,
                            cost      = cost,
                            remaining = number,
                            status    = 'approved'
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
                       cost   = cost,
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
        return None

    term.save()
    return term


def spreadsheet( email, password ):

   # Open Google Docs and get the spreadsheet
    spreadsheet = GoogleSpreadSheet( email, password )
    result = spreadsheet.getSpreadSheet(SPREADSHEET)
    if result == None or result.title.text != SPREADSHEET:
        print "Google Spreadsheet Error, Found: "  + result.title.text + \
              " Looking for: " + SPREADSHEET
        return None

    # Open the Organizers worksheet
    spreadsheet.getWorkSheet('Organization')
    organizations = spreadsheet.getCells()

    # Put all organizers in the database
    for organization in organizations:

        # Make sure all the necessary keys are present
        try:
            name      = organization['Organization'].rstrip()
            chapter   = organization['Chapter'].rstrip()
            email     = organization['Organizer Email'].rstrip()
            organizer = organization['Chapter Organizer'].rstrip()
            user_key  = organization['API User Key'].rstrip()
            org_id    = organization['Organizer ID'].rstrip()

        except KeyError, error:
            print "Key Error:" + str(error)
            continue

        # Test this to make sure user_id and organizer_id are OK
        app_key  = EVENTBRITE['APP_KEY' ]
        evb = EventbriteClient( tokens = app_key, user_key = user_key )

        try:
            events = evb.organizer_list_events( {'id':org_id} )
        except:
            print "Eventbrite ID Error:" + name +\
                  " user_id = " + str(user_key) +\
                  " organization_id = "+ str(org_id)

            ans = raw_input('Continue anyway (y/n)')
            if ans != 'y':
                pass
            else:
                continue

        else:
            # Check if you get an error from Eventbrite
            if 'error' in events:
                print 'Eventbrite Error: ' + events['error']['error_type'] + ' for ' + name +' = '+ org_id
                ans = raw_input('Continue anyway (y/n)')
                if ans != 'y':
                    pass
                else:
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

        # Get a list of the current sponsors
        buyer_list = d_chapter.buyers()

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
                email   = sponser['Sponsor Email'].rstrip()
                first   = sponser['Sponsor First Name'].rstrip()
                last    = sponser['Sponsor Last Name'].rstrip()
            except KeyError, error:
                print "Key Error:" + str(error)
                continue

            if 'Sponsor Company' in sponser:
                company = sponser['Sponsor Company'].rstrip()
            else:
                company = None
            if 'Sponsor Title' in sponser:
                title = sponser['Sponsor Title'].rstrip()
            else:
                title = None
            if 'Sponsor Website' in sponser:
                website = sponser['Sponsor Website'].rstrip()
            else:
                website = None
            if 'Sponsor Phone' in sponser:
                phone = sponser['Sponsor Phone'].rstrip()
            else:
                phone = None
                
            if 'Sponsor LinkedIn' in sponser:
                linkedin = sponser['Sponsor LinkedIn'].rstrip()
            else:
                linkedin = None
            
            if 'Sponsor Twitter' in sponser:
                twitter = sponser['Sponsor Twitter'].rstrip()
            else:
                twitter = None
                
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

            profile.company  = company
            profile.title    = title
            profile.website  = website
            profile.phone    = phone
            profile.linkedin = linkedin
            profile.twitter  = twitter
            
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

                # See if this term exists
                try:
                    term = Term.objects.get( deal = deal, buyer = user, status ='approved' )

                # If not create it
                except Term.DoesNotExist:
                    term = new_term( deal, user, term_type, cost )

                # Otherwise update the existing term
                else:
                    term = update_term( term, term_type, cost )

                    # Take them out of the buyer list
                    if user in buyer_list:
                        buyer_list.remove(user)

                # In order to get child object, you have to query the db
                term = Term.objects.get( deal = deal, buyer = user, status = 'approved' )
                cterm = term.get_child()
                if isinstance(cterm, Budget):
                    lb.budget = cterm.remaining
                    lb.save()

                print 'Deal: %-35s Buyer: %-40s %s:%s,%s'%\
                      ( deal.interest.interest,
                        user.email,
                        term_type[0],
                        term_type[1],
                        cost )


        #Check if anything left in the sponsor list
        for buyer in buyer_list:
            print "%s %s %s is no longer on the list"%(buyer.first_name,
                                                       buyer.last_name,
                                                       buyer.email      )
            ans = raw_input('Do you want to cancel his/her deals? (y/n)')
            if ans == 'y':
                terms =Term.objects.filter(buyer = buyer)
                for term in terms:
                    if term.status == 'approved' and\
                       term.deal.chapter == d_chapter:
                        term.canceled()
                        term.save()




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
