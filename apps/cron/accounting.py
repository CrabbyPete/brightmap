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

def connections_for( user, first_day, last_day ):
    connections = Connection.objects.for_user(user,[first_day,last_day])
    return connections


def send_email(user, invoice, details = None):
    return

def main():
    """
    Main program to do accounting for all lead buyers and organizers
    """
    # Bill for last month
    first_day = date.today().replace(day = 1)
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
        
        connections = connections_for( profile.user, first_day, last_day )
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
                print details['date'] + ' ' + details['chapter'] + ' ' + details['person'] + ' ' + details['email'] + ' ' + details['interest']
            
            print profile.user.first_name + ' ' + profile.user.last_name + ' Total: $' +str(total)
  
            # Create the invoice
           
            
            if total > 0: 
                # Create an invoice 
                invoice = Invoice( user = profile.user, 
                                   title = first_day.strftime("%B %Y"),
                                   cost = total, 
                                   first_day = first_day, 
                                   last_day = last_day 
                                 )
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
                
if __name__ == '__main__':
    main()
