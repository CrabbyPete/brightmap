#-------------------------------------------------------------------------------
# Name:        mail.py
# Purpose:     Support Amazon SES and STMP mail interfaces
#
# Author:      Douma
#
# Created:     14/08/2011
# Copyright:   (c) Douma 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

# Standard smpt interfaces such as gmail
from smtplib            import SMTP_SSL
from smtplib            import SMTP
from smtplib            import SMTPAuthenticationError
from email.mime.text    import MIMEText

# Support for Amazon SES
from boto               import ses


class Mailer(object):

    # Initialize with Gmail address and password
    def __init__( self, mailer     = 'smtp',
                        access_key = None,
                        secret_key = None,
                        user       = None,
                        password   = None,
                        server     = 'smtp.gmail.com'  ):


        self.mailer= mailer
        if mailer == 'amazon':
            self.ses = ses.SESConnection( aws_access_key_id     = access_key,
                                          aws_secret_access_key = secret_key
                                        )
        else:
            self.mail = self.email_connect( user     = user,
                                            password = password,
                                            server   = server     )

    # Connect to the gmail stmp server
    def email_connect( self,
                       user     = None,
                       password = None,
                       server   = 'smtp.gmail.com' ):

        em = SMTP(server, 587)

        em.set_debuglevel(False)
        em.ehlo()
        em.starttls()
        em.ehlo()
        em.login(user, password)
        return em

    # Mail the message. It will alway be from the current gmail address.
    def email_to( self, text, to, me, subject ):
        if self.mailer == 'amazon':
               return self.ses.send_email( me, subject, text, to )

        msg = MIMEText( text )
        msg['Subject'] = subject
        msg['From'] = me

        # To is a list of To addresses
        COMMASPACE = ', '
        msg['To'] = COMMASPACE.join(to)
        return self.mail.sendmail(me, to, msg.as_string())


def main():
    pass

if __name__ == '__main__':
    main()
