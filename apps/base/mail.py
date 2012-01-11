#-------------------------------------------------------------------------------
# Name:        mail.py
# Purpose:     Centralize email
#
# Author:      Douma
#
# Created:     14/08/2011
# Copyright:   (c) Douma 2011
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from django.template                import  loader, Context
from django.core.mail               import  EmailMultiAlternatives

from settings                       import SEND_EMAIL, SITE_BASE
from datetime                       import datetime

import logging
logger = logging.getLogger('main.py')



class Mail(object):
    """
    Mail class
    """

    # Initialize with Gmail address and password
    def __init__( self, senders, receivers, subject, template_name, bcc = None, **kwargs ):
        self.senders   = senders
        self.recievers = receivers
        self.subject   = subject
        if bcc:
            self.bcc = [bcc]
        else:
            self.bcc = []
        # Get the template
        template = loader.get_template('letters/'+template_name )
        
        # Set up the context
        if 'url' in kwargs:
            kwargs['url'] = SITE_BASE+kwargs['url']
        
        c = Context( kwargs )

        # Render the message and log it
        self.body = template.render(c)
        return
 
    def log(self, message):
        return datetime.today().strftime("%Y-%m-%d %H:%M")+ ',  ' + message

    
    def send( self, **kwargs ):
        if not SEND_EMAIL:
            return
        
        msg = EmailMultiAlternatives( subject    = self.subject,
                                      body       = self.body,
                                      from_email = self.senders,
                                      to         = self.receivers,
                                      bcc        = self.bcc.append('bcc@brightmap.com')
                                    )
        try:
            msg.send( fail_silently = False )
        except Exception, e:
            err = "Email Send Error %s" % ( e, )
            logger.error(self.log(err))
                
        return