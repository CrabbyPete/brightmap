# Import Python librariess
import                              django_header
from datetime                       import date, timedelta

# Import local library
from base.models                    import Profile, Connection, Invoice, Authorize
from settings                       import AUTHORIZE

# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes


def invoice_user( user, first_day, last_day ):
    
    cost = 0

    for connection in Connection.objects.for_buyer( user,[first_day,last_day] ):
        if connection.status == 'sent':
            cost += connection.term.cost
    
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
    
    invoice.cost = cost
    invoice.status = 'pending'
    invoice.save()
    return invoice 
            


CIM_API  = cim.Api( unicode(AUTHORIZE['API_LOG_IN_ID'] ),
                    unicode(AUTHORIZE['TRANSACTION_ID']) 
                  )
    

def bill_user( user, invoice ):
    try:  
        authorize = Authorize.objects.get( user = user )
    except Authorize.DoesNotExist:
        return
    
    try:
        response = CIM_API.create_profile_transaction(  amount = invoice.cost,
                                                        customer_profile_id = authorize.customer_id,
                                                        customer_payment_profile_id = authorize.profile_id,
                                                        profile_type = AUTH_ONLY
                                                     )
    except AuthorizeError:
        return 
                
    else:
        # Check to see it if its OK
        result = response.messages.result_code.text_.upper()
   
        if result == 'OK':
            invoice.status = 'paid'
        else:
            invoice.status = 'rejected'
            
        invoice.save()
    return
            

def main(month = None):
    """
    Main program to do accounting for all lead buyers and organizers
    """
    first_day = date.today().replace(day = 1)
    if  month:
        first_day = first_day.replace( month = int(month) )
    else:
        # Bill for last month
        first_day = first_day.replace( month = first_day.month - 1 )
    
    last_day  = first_day.replace (month = first_day.month + 1 ) - timedelta( days = 1 )
  
    print "Invoicing for the month of: " + first_day.strftime("%B %Y")
    
 
    # Get all the leadbuyers
    profiles = Profile.objects.filter( is_leadbuyer = True )
    for profile in profiles:
        invoice = invoice_user( profile.user, first_day, last_day )
        if invoice :
            print profile.user.first_name + ' ' + profile.user.last_name + " = " + str( invoice.cost )
            #bill_user( profile.user, invoice )

 
                

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
    
    main( month )
