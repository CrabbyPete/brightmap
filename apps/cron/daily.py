# Django Imports
import django_header
from django.core.urlresolvers       import  reverse


# Python Imports
import optparse
from datetime                       import  date, datetime, timedelta

# Local Imports
from base.models                    import  Expire, Cancel
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
            

if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    
    # Add options for debugging
    op.add_option('--accounting', default = False, action="store_true", help = 'Run accounting')
    op.add_option('--trials',     default = False, action="store_true", help = 'Check trial deal expiration')
    op.add_option('--auto',       default = False, action="store_true", help = 'Automatically bill')
    op.add_option('-m',           dest = 'month',  action="store",      help = 'Month number to bill')
    (opts,args) = op.parse_args()

    # Check if options were set
    if opts.accounting:
        if opts.month:
            month = opts.month
        else:
            month = None
        
        accounting(month = month)
        
    
    if opts.trials:
        check_expired()
        
 


    

