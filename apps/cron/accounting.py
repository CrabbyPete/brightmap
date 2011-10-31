#-------------------------------------------------------------------------------
# Name:        Accounting
# Purpose:
#
# Author:      Douma
#
# Created:     23/09/2011
# Copyright:   (c) Douma 2011
#-------------------------------------------------------------------------------
# Import Python librariess
import                              django_header
import                              calendar
from datetime                       import date, datetime

# Import local library
from base.models                    import *
from settings                       import AUTHORIZE

# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes

def connections_for( user, month ):
    dow,last_day = calendar.monthrange( month.year, month.month )
    first = month.replace( day = 1 )
    last  = first.replace( month = first.month + 1 )

    connections = Connection.objects.for_user(user,[first,last])
    return connections


def send_email(user, invoice, details = None):
    return

def main():
    """
    Main program to do accounting for all lead buyers and organizers
    """
    # Bill for last month
    month = datetime.today()
    month = month.replace( month = month.month - 1)

    print "Invoicing for the month of: " + month.strftime("%B %Y")
    
   # Initialize the API class
    cim_api = cim.Api( unicode(AUTHORIZE['API_LOG_IN_ID']),
                       unicode(AUTHORIZE['TRANSACTION_ID']) 
                      )
    

    # Get all the leadbuyers
    profiles = Profile.objects.filter( is_leadbuyer = True )
    for profile in profiles:

        invoice = 0
        itemize = []
        
        connections = connections_for( profile.user, month )
        if connections != None:
            for connection in connections:
                invoice += connection.term.cost
                details = { 'date'     :connection.date.strftime("%Y-%m-%d"),
                            'chapter'  :connection.survey.event.chapter.name,
                            'person'   :connection.survey.attendee.first_name + ' '  + connection.survey.attendee.last_name,
                            'email'    :connection.survey.attendee.email,
                            'interest' :connection.survey.interest.interest
                          }
                itemize.append(details)
                print details['date'] + ' ' + details['chapter'] + ' ' + details['person'] + ' ' + details['email'] + ' ' + details['interest']
            print profile.user.first_name + ' ' + profile.user.last_name + ' Total: $' +str(invoice)
  
            
            if invoice > 0: 
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
                    send_email(user, invoice )
                else:
                    pass
                
if __name__ == '__main__':
    main()
