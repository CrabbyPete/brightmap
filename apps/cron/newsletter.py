# Import system stuff
import os, sys, uuid, time, re
from datetime import datetime

import cProfile

from os.path                    import abspath, dirname, join,split
from site                       import addsitedir
from email.mime.text            import MIMEText

# Set up the environment to run on it own.
APP_ROOT, tail = split(abspath(dirname(__file__)))
PROJECT_ROOT, tail = split(APP_ROOT)

sys.path.insert(0,PROJECT_ROOT)
sys.path.insert(0,APP_ROOT)


from django.core.management     import setup_environ
import settings
setup_environ(settings)

from django.db.models           import Q
from django.core.mail           import send_mail,EmailMessage
from django.contrib             import auth
from django.contrib.auth.models import User
from django.template            import loader, Context

# Import local stuff
from base.models                import *
from pycron                     import pycron
from mail                       import Mailer

"""
# Open SMTP emailer
mailer  = Mailer( server   = settings.EMAIL_HOST,
                  user     = settings.EMAIL_HOST_USER,
                  password = settings.EMAIL_HOST_PASSWORD
                )
"""
"""
# Open SMTP emailer
mailer  = Mailer( server   = 'smtp.sendgrid.net',
                  user     = 'brightmap',
                  password = '8jcgjg93j'
                )
"""

# Open Amazon emailer
mailer  = Mailer ( mailer = 'amazon',
                   access_key = settings.AMAZON['AccessKeyId'],
                   secret_key = settings.AMAZON['SecretKey']
                 )


def report_interests(date = None):
    """
    Report number of interests for each event
    """

    # Return a dictionary of events and interests
    report = {}
    if date == None:
        today = datetime.today()
    else:
        today = date

    # Get all organizers
    organizations = Organization.objects.all()
    for organization in organizations:
        for chapter in organization.chapters():

            # Get all the events for this organization/chapter
            for event in chapter.events():

                # Ignore old events
                delta = event.date - today
                if delta.days < 0:
                    continue

                # Get all the interests for this event
                interests = event.interests()
                report[event] = interests

    # You are done return the report
    return report


def cronjob():
    date = datetime.today()
    print 'Mailing @' + date.strftime("%Y-%m-%d %H:%M")

    qry = Profile.objects.filter( newsletter = True, is_leadbuyer = True )

    # Send email to every user who subscibes
    spam=[]

    # Get the latest report
    # This is for testing
    date = datetime.strptime('2011-08-01', "%Y-%m-%d")
    report = report_interests( date )
    leads = Interest.objects.leads()

    # Get who gets the letter
    for profile in qry:
        spam.append(profile.user.email)

    # Email the message
    spam = ['pete.douma@gmail.com','graham@ultralightstartups.com']

    # Create the messsage from the email template
    c = Context({ 'date'  : date,
                  'leads' : leads,
                  'report': report
                })

    t = loader.get_template('letters/newsletter.tmpl')
    message = t.render(c)
    subject = "BrightMap Leads for the week of " + date.strftime("%Y-%m-%d")

    mailer.email_to( message,
                     spam,
                     'newsletter@brightmap.com',
                     subject
                    )
    return


def main():
    # Set the cron job to send mail every day at 12:00AM
    cron = pycron(latency = 30)
    cron.add_job('*/2 * * * * *', cronjob )

    # Continually poll
    while True:
        time.sleep(2)
        for call in cron.get_matched_jobs():
            call()

if __name__ == "__main__":
    main()

