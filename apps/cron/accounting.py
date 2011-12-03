# Import Python librariess
import                              django_header
from datetime                       import datetime, date, timedelta

# Import local library
from base.models                    import Profile, Connection, Authorize, Invoice
from settings                       import AUTHORIZE

# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes

INVOICE = True 


def send_email(user, invoice, details = None):
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
    
    # Initialize the API class
    cim_api = cim.Api( unicode(AUTHORIZE['API_LOG_IN_ID']),
                       unicode(AUTHORIZE['TRANSACTION_ID']) 
                      )
    

    # Get all the leadbuyers
    profiles = Profile.objects.filter( is_leadbuyer = True )
    for profile in profiles:

        total = 0
        itemize = []
        print profile.user.first_name + ' ' + profile.user.last_name
        
        connections = Connection.objects.for_buyer(profile.user,[first_day,last_day])
        if connections != None:
            for connection in connections:
                total += connection.term.cost
                details = { 'date'     :connection.date.strftime("%Y-%m-%d"),
                            'chapter'  :connection.survey.event.chapter.name,
                            'person'   :connection.survey.attendee.first_name + ' '  + connection.survey.attendee.last_name,
                            'email'    :connection.survey.attendee.email,
                            'interest' :connection.survey.interest.interest
                          }
                itemize.append(details)
                print details['date'] + ' ' + details['chapter'] + ' ' + details['person'] + ' ' +\
                      details['email'] + ' ' + details['interest'] + ' ' + str( connection.term.cost )
            
            print profile.user.first_name + ' ' + profile.user.last_name + ' Total: $' +str(total)
  
            # Create the invoice
            if total > 0 and INVOICE: 
                title = first_day.strftime("%B %Y")
                
                # See if there is an existing invoice for this month
                try:
                    invoice = Invoice.objects.get( user      = profile.user,
                                                   title     = title,
                                                   first_day = first_day,
                                                   last_day  = last_day  )
                except Invoice.DoesNotExist:
                    # Create an invoice 
                    invoice = Invoice( user      = profile.user, 
                                       title     = title,
                                       cost      = total, 
                                       first_day = first_day, 
                                       last_day  = last_day 
                                     )
                else:
                    invoice.cost = total
                
                invoice.save()
            
                # Try and bill to the credit card
                try:  
                    authorize = Authorize.objects.get( user = profile.user )
                except Authorize.DoesNotExist:
                    continue
                try:
                    response = cim_api.create_profile_transaction( amount = invoice,
                                                                   customer_profile_id = authorize.customer_id,
                                                                   customer_payment_profile_id = authorize.profile_id,
                                                                   profile_type = AUTH_ONLY
                                                                  )
                except AuthorizeError, e:
                    continue
                
                else:
                    # Check to see it if its OK
                    result = response.messages.result_code.text_.upper()
   
                if result == 'OK':
                    invoice.status = 'paid'
                    
                    send_email(profile.user, invoice )
                else:
                    invoice.status = 'rejected'
                invoice.save()
                

import optparse
if __name__ == '__main__':
    op = optparse.OptionParser( usage="usage: %prog " +" [options]" )
    # Add options for debugging
    op.add_option('-d', action="store_true", help = 'Debug no emails sent')
    op.add_option('-p', action="store_true", help = 'Prompt to send')
    op.add_option('-m', action="store_true", help = 'Month number to start')

    opts,args = op.parse_args()

    # Check if options were set

    if opts.d:
        INVOICE = False
    else:
        INVOICE = True

    if opts.p:
        PROMPT = True
    else:
        PROMPT = False
    
    if opts.m:
        month = args[0]
    else:
        month = None
    
    main( month )
