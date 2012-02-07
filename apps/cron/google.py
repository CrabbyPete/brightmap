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
            gid = self.curr_id
        else:
            return None

        feed = self.gd_client.GetWorksheetsFeed(gid)
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

    def addRow(self, row ):
        entry = self.gd_client.InsertRow( row, self.curr_id, self.curr_wksht_id )
        if isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
            return True
        return False
        
        
    def editRow(self, index, row ):   
        feed = self.gd_client.GetListFeed(self.curr_id, self.curr_wksht_id)
        entry = self.gd_client.UpdateRow( feed.entry[index], row )
        if isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
            return True
        return False

                 
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


