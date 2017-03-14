import django_header

from datetime                   import datetime

# Import Django
from django.core.mail           import EmailMultiAlternatives
from django.template            import loader, Context

# Import local stuff
from base.models                import Profile, Interest
#from pycron                     import pycron
#from mail                       import Mailer


def report_interests ( date = None ):
    """
    Interests Report
    """
    report = {}
    interests = Interest.objects.all()
    for interest in interests:
        report[interest] = interest.events( open = True )

    """ For testing the template
    for interest, event  in report.items():
        print interest.interest

        for ev, count in event.items():
            print ev.describe + ':' + str(count)
            if ev.chapter.website:
                print ev.chapter.website
    """
    return report


def cronjob():
    date = datetime.today()
    print 'Mailing @' + date.strftime("%Y-%m-%d %H:%M")

    # Send email to every user who subscribes and is a leadbuyer
    bcc = []
    for profile in Profile.objects.filter( newsletter   = True,
                                           is_leadbuyer = True ):
        to =  '%s %s <%s>'% ( profile.user.first_name,
                              profile.user.last_name,
                              profile.user.email
                            )
        bcc.append(to)

    # Get the latest report
    report = report_interests()

    # Create the messsage from the email template
    c = Context({ 'date'  : date,
                  'report': report
                })

    # Create a text and html version
    text = loader.get_template('letters/newsletter.tmpl').render(c)
    html = loader.get_template('letters/newsletter.html').render(c)
    subject = "BrightMap Leads for the week of " + date.strftime("%Y-%m-%d")


    # TESTING TESTING TESTING TESTING
    spam = ['pete.douma@gmail.com']
    bcc  = ['newsletter@brightmap.com']
    msg = EmailMultiAlternatives( subject,
                                  text,
                                  'newsletter@brightmap.com',
                                  spam,
                                  bcc
                                )
    msg.attach_alternative(html, "text/html")
    #msg.send( fail_silently = False )
    return

"""
def main():
    # Set the cron job to send mail every day at 12:00AM
    cron = pycron(latency = 30)
    cron.add_job('* * * * * *', cronjob )

    # Continually poll
    while True:
        time.sleep(30)
        for call in cron.get_matched_jobs():
            call()

"""

if __name__ == "__main__":
    cronjob()

