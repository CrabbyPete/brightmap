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
from django.core.mail               import  EmailMessage

from settings                       import SEND_EMAIL, SITE_BASE
from datetime                       import datetime

import logging
logger = logging.getLogger('mail')


class Mail():
    """
    Mail class
    """
    body = ''
    subject = ''
    bcc = ['bcc@brightmap.com']

    # Initialize with Gmail address and password
    def __init__( self, sender, receivers, subject, template_name, bcc = None, **kwargs ):
        self.sender    = sender
        self.receivers = receivers
        self.subject   = subject

        self.bcc = ['bcc@brightmap.com','pete@brightmap.com']
        if bcc:
            self.bcc.extend(bcc)
        else:
            self.bcc = ['bcc@brightmap.com']


        # Get the template
        template = loader.get_template('letters/'+template_name )
        
        # Set up the context
        # Point to the correct URL
        if 'url' in kwargs:
            kwargs['url'] = SITE_BASE+kwargs['url']
            
        # Get all the arguments
        if 'kwargs' in kwargs:
            kwargs = kwargs['kwargs']
        
        c = Context( kwargs )

        # Render the message and log it
        self.body = template.render(c)
        return
 
    def log(self, message):
        return datetime.today().strftime("%Y-%m-%d %H:%M")+ ',  ' + message

    
    def send( self, **kwargs ):

        if not SEND_EMAIL:
            self.receivers = ['pete.douma@gmail.com']
            #self.bcc = ['test@brightmap.com']
            self.bcc = []
    
        msg = EmailMessage ( subject    = self.subject,
                             body       = self.body,
                             from_email = self.sender,
                             to         = self.receivers,
                             bcc        = self.bcc
                            )
        
        try:
            msg.send()
        except Exception, e:
            err = "Email Send Error " + str(e)
            logger.error(self.log(err))
            return False
           
        return True