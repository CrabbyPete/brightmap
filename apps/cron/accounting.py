# Import Python librariess
import                              django_header
import logging
logger = logging.getLogger('accounting')


from datetime                       import datetime, timedelta

# Django imports
from django.template                import loader, Context
from django.core.mail               import EmailMultiAlternatives

# Import local library
from base.models                    import Profile, Connection, Invoice, Authorize, Commission, Chapter
from settings                       import AUTHORIZE, SEND_EMAIL

# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY, AUTH_CAPTURE
from authorize.responses            import AuthorizeError, _cim_response_codes


def days_of_month (month = None):
    
    first_day = datetime.today().replace(day = 1)
    if  month:
        first_day = first_day.replace( month = int(month) )

    if first_day.month == 12:
        last_day = first_day.replace ( day = 31 )
    else:
        last_day = first_day.replace (month = first_day.month + 1 ) - timedelta( days = 1 )
    
    return first_day, last_day


def pay_commissions( invoice ):
    
    chapters = {}
    for connection in invoice.connections():
        chapter = connection.term.deal.chapter
        if chapter.pk in chapters:
            chapters[chapter.pk] += connection.term.cost
        else:
            chapters[chapter.pk] = connection.term.cost
    
    for chapter_pk in chapters.keys():
        
        if chapters[chapter_pk] <= 0:
            continue
        
        chapter = Chapter.objects.get( pk = chapter_pk )
        try:
            commission = Commission.objects.get( invoice = invoice, chapter = chapter )
        except Commission.DoesNotExist:
            commission = Commission(invoice = invoice, chapter = chapter)
        commission.cost = "%.2f"%( float( chapters[chapter_pk] ) * 0.45, ) 
        commission.save()

        
            
def invoice_user( user, first_day = None, last_day = None ):
    
    if not first_day:
        first_day,last_day = days_of_month()
        
    duplicates = []
    connections = Connection.objects.for_buyer( user,[first_day,last_day] )
    #cost = sum( connection.term.cost for connection in connections if connection.status == 'sent' )
    
    # Check for duplicate messages 
    cost = 0
    for connection in connections:
        if connection.status == 'sent':
            if connection.survey.attendee in duplicates:
                connection.status = 'duplicate'
                connection.save()
            else:
                cost = cost +  connection.term.cost
                duplicates.append( connection.survey.attendee )
    
 
    if not cost:
        return None
 
    title = first_day.strftime("%B %Y")
                
    # See if there is an existing invoice for this month
    try:
        invoice = Invoice.objects.get( user      = user,
                                       title     = title,
                                       first_day = first_day,
                                       last_day  = last_day  )
    except Invoice.DoesNotExist:
        # Create an invoice 
        invoice = Invoice( user      = user, 
                           title     = title,
                           first_day = first_day, 
                           last_day  = last_day 
                         )
    
    if invoice.status != 'paid':
        invoice.cost = cost
        invoice.status = 'pending'
        invoice.save()
    
    
    return invoice 
            

def bill_user( invoice ):
    cim_api  = cim.Api( unicode(AUTHORIZE['API_LOG_IN_ID'] ),
                        unicode(AUTHORIZE['TRANSACTION_ID']) 
                      )
    
    try:  
        authorize = Authorize.objects.get( user = invoice.user )
    except Authorize.DoesNotExist:
        invoice.status = 'unauthorized'
        invoice.save()
        return invoice
    
    try:
        response = cim_api.create_profile_transaction(  amount                      = invoice.cost,
                                                        customer_profile_id         = authorize.profile_id,
                                                        customer_payment_profile_id = authorize.payment_profile,
                                                        profile_type                = AUTH_CAPTURE,
                                                        invoice_number              = invoice.pk
                                                     )
    except AuthorizeError:
        invoice.status = 'unauthorized'
        invoice.save()
        return invoice
                
    else:
        # Check to see it if its OK
        result = response.messages.result_code.text_.upper()
   
        if result == 'OK':
            invoice.status = 'paid'
        else:
            invoice.status = 'rejected'
            
        invoice.save()
    return invoice
     
     
def notify_user( invoice ):
    # Set up the context
    c = Context({'invoice' :invoice })

    # Render the message and log it
    template = loader.get_template('letters/invoice.tmpl')
    message = template.render(c)

    subject = 'BrightMap Invoice: '+ invoice.title
    bcc = [ 'bcc@brightmap.com' ]
    from_email = '<invoice@brightmap.com>'

    to_email = [ '%s %s <%s>'% ( invoice.user.first_name, invoice.user.last_name, invoice.user.email ) ]
 

    # Send the email
    msg = EmailMultiAlternatives( subject    = subject,
                                  body       = message,
                                  from_email = from_email,
                                  to         = to_email,
                                  bcc        = bcc
                                )

    if SEND_EMAIL:
        try:
            msg.send( fail_silently = False )
        except:
            pass
 

def accounting( month = None, autobill = False ):
    """
    Update all the invoices for the month
    """
    if not month:
        print "Invoicing for the month of: " + datetime.today().strftime("%B %Y")
    else:
        first_day, last_day = days_of_month( month = month )
        print "Invoicing for the month of: " + first_day.strftime("%B %Y")
        
    for profile in Profile.objects.filter( is_leadbuyer = True ):
        user = profile.user
        if month:
            invoice = invoice_user( user, first_day = first_day, last_day = last_day )
        else:
            invoice = invoice_user( user )
        
        if not invoice:
            continue
 
        print profile.user.first_name + ' ' + profile.user.last_name + " = " + str( invoice.cost )
        
        # Bill them if its automatic
        if autobill:
            notify_user( invoice )
            bill_user( invoice )
        
   
def main(month = None):
    """
    Main program to do accounting for all lead buyers and organizers
    """
    accounting(month = month, autobill = False)

 
import optparse
if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    # Add options for debugging
    op.add_option('-d', action="store_true", help = 'Debug no emails sent')
    op.add_option('-p', action="store_true", help = 'Prompt to send')
    op.add_option('-m', action="store_true", help = 'Month number to start')

    opts,args = op.parse_args()

    # Check if options were set
    if opts.p:
        PROMPT = True
    else:
        PROMPT = False
    
    if opts.m:
        month = args[0]
    else:
        month = None
    
    main(month)
