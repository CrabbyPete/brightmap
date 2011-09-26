#-------------------------------------------------------------------------------
# Name:        Accounting
# Purpose:
#
# Author:      Douma
#
# Created:     23/09/2011
# Copyright:   (c) Douma 2011
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import              django_header
import              calendar

from datetime               import date, datetime
from base.models            import *


def connections_for( user, month ):
    dow,last_day = calendar.monthrange( month.year, month.month )
    first = month.replace( day = 1 )
    last  = first.replace( month = first.month + 1 )

    connections = Connection.objects.for_user(user,[first,last])
    return connections

def main():
    """
    Main program to do accounting for all lead buyers and organizers
    """

    # First get all the leadbuyers
    month = datetime.today()
    #month = day.replace( month = day.month - 1)

    profiles = Profile.objects.filter( is_leadbuyer = True )
    for profile in profiles:

        invoice = 0
        print profile.user.first_name + ' ' + profile.user.last_name
        connections = connections_for( profile.user, month )
        if connections != None:
            for connection in connections:
                invoice += connection.term.cost
                print connection.date.strftime("%Y-%m-%d") + " " +\
                      str(connection.survey.event.chapter.name) + " "+\
                      connection.survey.attendee.email

            print "Total: $"+str(invoice)


if __name__ == '__main__':
    main()
