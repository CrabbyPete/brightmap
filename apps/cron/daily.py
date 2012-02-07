# Django Imports
import django_header
from django.core.urlresolvers       import  reverse
from google                         import  GoogleSpreadSheet

# Python Imports
import optparse
from datetime                       import  date, datetime, timedelta

# Local Imports
import settings
from base.models                    import  ( Term, 
                                              Expire, 
                                              Cancel, 
                                              Authorize, 
                                              Chapter, 
                                              Commission, 
                                              Connection,
                                              LeadBuyer
                                            )

from base.mail                      import  Mail 
from accounting                     import  accounting


TODAY = datetime.today()

def log( message ):
    """
    Time stamp all messages
    """
    return TODAY.strftime("%Y-%m-%d %H:%M")+ ',  ' + message
    

def warn_user( term, warning = False ):
    """
    Warn a deal buyer that their deal has changed, if warning is about to expire
    """
    child = term.get_child()
    if isinstance(child, Expire) or isinstance(term, Expire):
        buyer     = term.buyer
        organizer = term.deal.chapter.organizer
        if warning:
            template_name = 'expire_warning.tmpl'
            subject  = 'BrightMap Trial Expiring: ' + term.deal.chapter.name
            connects = term.connections()
        else:
            template_name = 'expire_notice.tmpl'
            subject  = 'BrightMap Trial Expired: ' + term.deal.chapter.name
            connects = term.connections()

            
        msg = Mail( organizer.email,
                    [buyer.email], 
                    subject = subject, 
                    template_name = template_name, 
                    bcc = [organizer.email], 
                    buyer = buyer,
                    term  = term,
                    connections = connects,
                    url   = reverse('lb_dash')
                   )
        
        result = msg.send()
        if not result:
            print log('Error sending email to %s for deal expiration'%( buyer.email,))
        
        # If this is not warning, delete the trial and make it a standard deal
        if not warning:
            term.canceled()
            new_term = Cancel(  deal  = term.deal,
                                cost  = 20,
                                buyer = term.buyer,
                                exclusive = False,
                                status = 'approved'
                             )
            new_term.save()
        
    return

def check_expired():
    expires = Expire.objects.filter(status='approved')
    for expire in expires:
        
        # Make sure they got some connections
        if len( expire.connections() ) == 0:
            continue
        
        day =  date.today()
        warning_day = day - timedelta( days = 5 )
        if expire.date < date.today():
            print log( 'Converting trial deal for '+\
                       expire.buyer.last_name+','+expire.buyer.first_name+ ' ' +\
                       expire.date.strftime("%Y-%m-%d") + ' '+\
                       expire.deal.chapter.name +\
                       ' with ' + str( len(expire.connections()) )+ ' connections: '
                     )

            warn_user(expire)
        
        # Warn the user 5 days before. Make sure main is only run once a day.
        elif expire.date == warning_day:
            print str( expire.pk ) + ' ' + expire.buyer.last_name +' ' + expire.date.strftime("%Y-%m-%d %H:%M")
            warn_user( expire, warning = True )
            
def convert_pending_deals():
    terms = Term.objects.filter( status = 'pending' )
    
    for term in terms:
        # Check if the user is approved 
        try:
            authorize = Authorize.objects.get( user = term.buyer )
        except Authorize.DoesNotExist:
            continue
        if not authorize.profile_id:
            continue
        
        # If this is a Standard or Exclusive deal
        child = term.get_child()
        
        # Approve Standard deals
        if isinstance(child,Cancel):
            if child.exclusive:
                continue
    
        # Check trial deals, only allow 1 per buyer, 1 per chapter
        elif isinstance(child,Expire):
            
            expires = Expire.objects.filter( buyer = term.buyer, status='approved' )
            if len ( expires ) >= settings.MAX_TRIALS:
                continue
            
            # Check the number of trials the organizer has
            expires = Expire.objects.filter ( deal = term.deal, status='approved' )
            if len ( expires ) > 0:
                continue
            
        term.status = 'approved'
        term.save()
        print "Converting deal: " + term.deal.chapter.name + '-' +\
                                    term.deal.interest.interest + ' for ' +\
                                    term.buyer.first_name + ' ' + term.buyer.last_name 
                                    
        subject = term.deal.chapter.name + ' sponsorship approved'
        mail = Mail( "deals@brightmap.com",
                     [term.buyer.email, term.deal.chapter.organizer.email],
                     subject,
                     'deal_status.tmpl',
                     term = term,
                     url  = reverse('lb_dash')
                    )
        mail.send()

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
    
    warning_level = float(leadbuyer.budget) * 0.90
    if total >= warning_level:
        buyer     = term.buyer
        #organizer = term.deal.chapter.organizer
 
        mail = Mail( 'notice@brightmap.com',
                     [buyer.email], 
                     'Budget',
                     'budget_notice.tmpl',
                     bcc = None,
                     buyer = buyer,
                     budget = leadbuyer.budget,
                     total = total,
                     connections = connections,
                     url   = reverse('lb_dash')
                    )
        
        mail.send()

    return True

SPREADSHEET = 'Brightmap-metrics'

def open_spreadsheet( email, password ):
    # Open Google Docs and get the spreadsheet
    spreadsheet = GoogleSpreadSheet( email, password )
    result = spreadsheet.getSpreadSheet(SPREADSHEET)
    if result == None or result.title.text != SPREADSHEET:
        print "Google Spreadsheet Error, Found: "  + result.title.text + \
              " Looking for: " + SPREADSHEET
        return None
    
    # Open the Organizers worksheet
    spreadsheet.getWorkSheet('Organizations')
    return spreadsheet

MONTH =  ['jan','feb','mar','apr','may','june','jul','aug','sep','oct','nov','dec']
def metric( email, password ):
    chapters = Chapter.objects.all()
    spreadsheet = open_spreadsheet( email, password )
    cells = spreadsheet.getCells()

    for chapter in chapters:
        if not chapter.configured():
            continue
        row = dict()
        row ['date'] = datetime.today().strftime("%d/%m/%Y")
        row ['organization'] = chapter.name

        c_trials = 0
        c_standard = 0
        c_sponsored = 0
        for deal in chapter.deals():
            for term in deal.active():
                if term.cost > 0:
                    c_standard += 1
                elif term.cost == 0 and term.exclusive:
                    c_sponsored += 1
                else:
                    try:
                        e = term.expire
                    except:
                        pass
                    else:
                        c_trials += 1
        
        total_connections = 0
        paid_connections  = 0
        total_attendees   = 0

        months = [0 for x in range(12)]
        events = chapter.events()
        for event in events:
            attending = len( event.attendees() )
            
            if attending == 0:
                continue
                
            total_attendees += attending
            month = event.date.month - 1
            
            for connect in event.connections():
                total_connections += 1
                if connect.term.cost > 0:
                    paid_connections += 1
                    months[month] += 1
   
        if total_attendees > 0: 
            ratio = float( paid_connections ) / float( total_attendees )
        else:
            ratio = 0.0
            
        total_events = len(events)
        if total_events > 0:
            aver  = float(total_attendees)/float(total_events)
            dollars = (float(paid_connections) * 20)/float(total_events)
        else:
            aver  = 0
            dollars = 0
            
        row['sponsored']   = str(c_sponsored)
        row['paid']        = str(c_standard)
        row['trial']       = str(c_trials)
        row['connections'] = str( total_connections ) 
        row['billable']    = str( paid_connections )
        row['events']      = str(total_events)
        row['attendees']   = "%.2f" % aver
        row['ratio']       = "%.2f" % ratio
        row['dollars']     = "%.2f" % dollars
        
        for m,name in enumerate(MONTH): 
            row[name] = str( months[m] )
        
        found = False
        for index, cell in enumerate(cells):
            if row['organization'] == cell['organization']:
                spreadsheet.editRow( index, row )
                found = True
                break
        if not found:
            spreadsheet.addRow( row )
        
    return

if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    
    # Add options for debugging
    op.add_option('--trials',     default = False,  action="store_true", help = 'Check trial deal expiration')
    op.add_option('--pending',    default = False,  action="store_true", help = 'Convert pending deals')
    op.add_option('--accounting', default = False,  action="store_true", help = 'Run accounting')
    op.add_option('-a',           default = False,  action="store_true", help = 'Automatically bill')
    op.add_option('-m',           dest = 'month',   action="store",      help = 'Month number to bill')
    op.add_option('-y',           dest = 'year',    action="store",      help = 'Year number to bill')
    op.add_option('--metric',     default = False,  action="store_true", help = "Run metrics")
    op.add_option('-e',           dest = 'email',   action="store",      help = "Email address for Google Spreadsheet")
    op.add_option('-p',           dest = 'password',action="store",      help = "Password for Google Spreadsheet")
    
    
    (opts,args) = op.parse_args()

    # Check if options were set
    if opts.metric:
        metric(opts.email, opts.password)
        
    if opts.accounting:
        if opts.month:
            month = opts.month
            if opts.year:
                year = opts.year
        else:
            month = None
            year  = None
        
        accounting(month = month, year = year )
        
    # Convert trial deals to standard one
    if opts.trials:
        check_expired()
    
    # Convert pending deals to approved ones
    if opts.pending:
        convert_pending_deals()
        
 


    

