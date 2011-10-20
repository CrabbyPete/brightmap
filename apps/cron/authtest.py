import                              django_header

# Import local library
from base.models                    import *
from settings                       import AUTHORIZE

# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes

def main(first_name, last_name):

    try:
        user = User.objects.get( first_name = first_name, last_name = last_name )
    except User.DoesNotExist:
        return
    
    profile = user.get_profile()
  
    try:  
        authorize = Authorize.objects.get( user = profile.user )
    except Authorize.DoesNotExist:
        return
    
       # Initialize the API class
    cim_api = cim.Api( unicode(AUTHORIZE['API_LOG_IN_ID']),
                       unicode(AUTHORIZE['TRANSACTION_ID']) 
                      )
    
    try:
        response = cim_api.create_profile_transaction( amount = 10.00,
                                                       customer_profile_id = authorize.profile_id,
                                                       customer_payment_profile_id = authorize.payment_profile,
                                                       profile_type = AUTH_ONLY,
                                                       invoice_number = unicode(1000),
                                                       description = u'Test invoice',
                                                     )
    except AuthorizeError, e:
        print e
        return
                
    else:
        # Check to see it if its OK
        result = response.messages.result_code.text_
   
        if result == 'Ok':
            pass
        else:
            print "Result:"+result
                
import optparse             
if __name__ == '__main__':
    
    op = optparse.OptionParser( usage="usage: %prog " +
                                "<First Name> <Last Name>" )

    opts,args = op.parse_args()

    if len(args) >=2:
        first    = args[0]
        last = args[1]
    
    main(first, last)