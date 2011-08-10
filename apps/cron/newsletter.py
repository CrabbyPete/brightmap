# Import system stuff
import os, sys, uuid, time, re

from os.path                    import abspath, dirname, join,split
from site                       import addsitedir

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

def cronjob(job):
    if len(job) == 0:
        return

    print 'Mailing @' + time.strftime("%I:%M:%S %p", time.localtime())

    qry = Profile.objects.filter(newsletter=True)

    # Send email to every user who subscibes
    spam=[]
    for profile in qry:
        spam.append(profile.user.email)

    leads = Lead.objects.filter(posted=False)
    for lead in leads:
        lead.posted = True
        lead.save()

    # Personalize text and html version with first name
    c = Context({'leads':leads})
    text = loader.get_template('vendorneeded.txt').render(c)
    msg = EmailMessage("VendorNeeded Bulletin",text,'bulletin@vendorneeded.net', spam )
    msg.send(fail_silently = False)

    return


def main():

    # Set the cron job to send mail every day at 12:00AM
    cron = pycron(latency = 30)
    cron.add_job('*/2 * * * * *', 'anyleads')

    # Continually poll
    while True:
        time.sleep(30)
        cronjob( cron.get_matched_jobs())


if __name__ == "__main__":
    main()