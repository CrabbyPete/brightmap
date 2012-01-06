import urllib2

from django.utils import simplejson as json

import settings

#PAYPAL_ENDPOINT = 'https://svcs.sandbox.paypal.com/AdaptivePayments/' # sandbox
PAYPAL_ENDPOINT = 'https://svcs.paypal.com/AdaptivePayments/' # production


#PAYPAL_APPLICATION_ID = 'APP-80W284485P519543T' # sandbox only
PAYPAL_APPLICATION_ID = 'APP-3FY99092X0259451U'



class Pay( object ):
    def __init__( self, email, amount, secondary_receiver=None, ipn_url=None, shipping=False ):
        headers = {
                   'X-PAYPAL-SECURITY-USERID': settings.PAYPAL['USERID'], 
                   'X-PAYPAL-SECURITY-PASSWORD': settings.PAYPAL['PASSWORD'], 
                   'X-PAYPAL-SECURITY-SIGNATURE': settings.PAYPAL['SIGNATURE'], 
                   'X-PAYPAL-REQUEST-DATA-FORMAT': 'JSON',
                   'X-PAYPAL-RESPONSE-DATA-FORMAT': 'JSON',
                   'X-PAYPAL-APPLICATION-ID': PAYPAL_APPLICATION_ID,
                   'X-PAYPAL-DEVICE-IPADDRESS': '127.0.0.1',
                   }

        data = {
                'currencyCode': 'USD',
                'returnUrl': 'http://brightmap.com',
                'cancelUrl': 'http://brightmap.com',
                'requestEnvelope': { 'errorLanguage': 'en_US' },
                } 
        data['actionType'] = 'PAY'
        data['receiverList'] = { 'receiver': [ { 'email': email, 'amount': '%f' % amount } ] }  
        data['senderEmail'] = 'paypal@brightmap.com'
        self.raw_request = json.dumps(data)
        request = urllib2.Request( "%s%s" % ( PAYPAL_ENDPOINT, "Pay" ), data=self.raw_request, headers=headers )
        self.raw_response = urllib2.urlopen( request ).read() 
  
        print  "response was: %s" % (self.raw_response,) 
        self.response = json.loads( self.raw_response )
        
        if self.response['responseEnvelope']['ack'] == 'Success':
            self.payKey =self.response['payKey'] 
        
        pass

