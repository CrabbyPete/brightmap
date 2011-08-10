#-------------------------------------------------------------------------------
# Name:        Ultralight Startup Class
# Purpose:
#
# Author:      Douma
#
# Created:     08/05/2011
#-------------------------------------------------------------------------------


import sys
import re
import os.path
import getopt
import getpass
import urllib


import gdata.docs.service
import gdata.spreadsheet.service

import smtplib

import oauth2 as oauth
import oauth2.clients.imap as imaplib

#from smtplib           import SMTP_SSL as SMTP         # this invokes the secure SMTP protocol (port 465, uses SSL)
from smtplib            import SMTP                     # use this for standard SMTP protocol   (port 25, no encryption)
from smtplib            import SMTPAuthenticationError
from email.mime.text    import MIMEText                 # Import the email modules we'll need

import gdata.docs.data
import gdata.docs.client

# Use this setting to actually send emails
#from settings           import EMAIL

class GoogleSpreadSheet():

    def __init__(self, email, password):
        self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
        self.gd_client.email = email
        self.gd_client.password = password
        self.gd_client.source = 'Spreadsheets GData Sample'
        self.gd_client.ProgrammaticLogin()

        self.curr_id = None
        self.curr_wksht_id = ''
        self.list_feed = None


    # Get the spreadsheet
    def getSpreadSheet(self, name):
        feed = self.gd_client.GetSpreadsheetsFeed()
        #self.printFeed(feed)
        for entry in feed.entry:
            if name in entry.title.text:
                self.curr_id = entry.id.text.split('/')[-1]
                return entry
        return None

    # Get the work for each name
    def getWorkSheet(self, name):
        if self.curr_id != None:
            id = self.curr_id
        else:
            return None

        feed = self.gd_client.GetWorksheetsFeed(id)
        #self.printFeed(feed)
        for entry in feed.entry:
            if name in entry.title.text:
                self.curr_wksht_id = entry.id.text.split('/')[-1]
                return entry
        return None

    # Get column and row eq. A1 = column A row 1
    def getBox(self, value):
        row =''.join(i for i in value if i.isdigit())
        col =''.join(i for i in value if i.isupper())
        return row,col

    # Return a dictonary for each cell. Row 1 must be titles
    def getCells(self):
        feed = self.gd_client.GetCellsFeed(self.curr_id, self.curr_wksht_id)
        #self.printFeed(feed)
        spreadsheet = []
        rows = {}
        columns = {}
        c_row = 1
        c_col = 0

        # Get each cell
        for entry in feed.entry:
            row, col = self.getBox( entry.title.text )

            # Get all the content from 1 row
            if row == str(c_row):

                # Column 1 has the headers make a list of headers
                if row == '1':
                    columns[col] = entry.content.text

                # Create a dictionary of cell content
                else:
                    rows[columns[col]] = entry.content.text

            # Next row start again
            else:
                # The first one will be empty since we took out the headers
                if len(rows) > 0:
                    spreadsheet.append(rows)

                # Start a new dictonary for this row
                rows = dict({columns[col]:entry.content.text})
                c_row += 1

        # Get the last one
        if len(rows) > 0:
            spreadsheet.append(rows)

        return spreadsheet


    def printFeed(self, feed):
        for i, entry in enumerate(feed.entry):
            if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
                print '%s %s\n' % (entry.title.text, entry.content.text)
            elif isinstance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
                print '%s %s %s' % (i, entry.title.text, entry.content.text)
                print 'Contents:'
                for key in entry.custom:
                    print '  %s: %s' % (key, entry.custom[key].text)
                    print '\n',
            else:
                print '%s %s\n' % (i, entry.title.text)


class Gmailer(object):

    # Initialize with Gmail address and password
    def __init__( self, email, password ):
        self.gmail = self.email_connect( username = email,
                                         password = password )

    # Connect to the gmail stmp server
    def email_connect( self,
                       server = 'smtp.gmail.com',
                       username = None,
                       password = None            ):

        em = SMTP('smtp.gmail.com', 587)

        em.set_debuglevel(False)
        em.ehlo()
        em.starttls()
        em.ehlo()
        em.login(username, password)
        return em

    # Mail the message. It will alway be from the current gmail address.
    def email_to( self, text, to, me, subject ):
        msg = MIMEText( text )
        msg['Subject'] = subject
        msg['From'] = me

        # To is a list of To addresses
        COMMASPACE = ', '
        msg['To'] = COMMASPACE.join(to)
        if not self.gmail:
            self.gmail = email_connect(username = username, password = password)
        """
        if EMAIL:
            pdb.settrace()
            self.gmail.sendmail(me, to, msg.as_string())
        """

class GoogleOAuth(object):

    request_token_url = 'https://www.google.com/accounts/OAuthGetRequestToken'
    access_token_url  = 'https://www.google.com/accounts/OAuthGetAccessToken'
    authorization_url = 'https://www.google.com/accounts/OAuthAuthorizeToken'

    def __init__( self, api_key, app_secret, callback = None ):
        self.consumer  = oauth.Consumer(api_key, app_secret)
        self.callback = callback

    def get_tokens(self):
        kwargs = {'scope':'https://mail.google.com/'}
        req = oauth.Request.from_consumer_and_token( self.consumer,
                                            http_url = self.request_token_url,
                                            parameters = kwargs
                                                   )

        req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), self.consumer, None)
        data = urllib.urlencode(req)

        url='%s?%s'%(self.request_token_url, data)
        response = urllib.urlopen(url)

        data = response.read()
        token = oauth.Token.from_string(data)
        pdb.set_trace()
        data = oauth.Request.from_token_and_callback( token  = token,
                                             callback = self.callback,
                                             http_url = self.authorization_url )

        data = urllib.urlencode(data)
        url='%s?%s'%(self.authorization_url, data)
        return url, token

    def callback(self, request):
        if 'oauth_token' in request.values:
            oauth_token = request.values['oauth_token']

        token = oauth.Token( self.oauth_token, self.oauth_secret )

        if 'oauth_verifier' in request.values:
            token.set_verifier(request.values['oauth_verifier'])

        self.client = oauth.Client(self.consumer, token)

        # Step 2. Request the authorized access token from Provider.
        resp, content = self.client.request(self.access_token_url, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response from Provider.")

        parts = dict(cgi.parse_qsl(content))
        return parts

