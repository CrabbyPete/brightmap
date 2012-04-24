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
from django.core.mail               import  EmailMessage, get_connection

from settings                       import SEND_EMAIL, SITE_BASE
from datetime                       import datetime


class Mail():
    """
    Mail class
    """
    def __init__(self):
        """
        Open the connection once  
        """
        self.connection = get_connection()
        self.connection.open()
        
    def __del__(self):
        """
        Close the connection when done
        """
        self.connection.close()
        
        
    # Initialize with Gmail address and password
    def message( self, sender, receivers, subject, template_name, bcc = None, **kwargs ):
        self.sender    = sender
        self.receivers = receivers
        self.subject   = subject

        self.bcc = ['bcc@brightmap.com']
        if bcc:
            self.bcc.extend(bcc)
        else:
            self.bcc = ['bcc@brightmap.com']


        # Get the template
        template = loader.get_template('letters/'+template_name )
        
        # Set up the context
        if 'url' in kwargs:
            kwargs['url'] = SITE_BASE+kwargs['url']
        if 'kwargs' in kwargs:
            kwargs = kwargs['kwargs']
        
        c = Context( kwargs )

        # Render the message and log it
        self.body = template.render(c)

        if not SEND_EMAIL:
            self.receivers = ['pete.douma@gmail.com']
            #self.bcc = ['test@brightmap.com']
            self.bcc = []
    
        msg = EmailMessage ( subject    = self.subject,
                             body       = self.body,
                             from_email = self.sender,
                             to         = self.receivers,
                             bcc        = self.bcc,
                             connection = self.connection
                            )
        
        try:
            msg.send()
        except Exception, e:
            err = "Email Send Error " + str(e)
            return False
           
        return True