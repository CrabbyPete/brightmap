from difflib                                import SequenceMatcher
from datetime                               import date

from django.db                              import models
from django.db.models                       import Q
from django.contrib.auth.models             import User
from django.contrib.localflavor.us.models   import PhoneNumberField

class Profile( models.Model ):
    """
    Addition user profile information to supplement django User
    """
    user       = models.ForeignKey( User )
    address    = models.CharField( max_length = 255, blank = True, null = True )
    phone      = PhoneNumberField(                   blank = True, null = True )

    company    = models.CharField( max_length = 100, blank = True, null = True )
    title      = models.CharField( max_length = 100, blank = True, null = True )

    website    = models.URLField(                    blank = True, null = True )
    twitter    = models.URLField(                    blank = True, null = True )
    linkedin   = models.URLField(                    blank = True, null = True )
    photo      = models.URLField(                    blank = True, null = True )

    is_organizer  = models.BooleanField( default = False )
    is_leadbuyer  = models.BooleanField( default = False )
    is_attendee   = models.BooleanField( default = False )

    newsletter    = models.BooleanField( default = True )

    def __unicode__(self):
        return self.user.email

class Organization( models.Model ):
    """
    Base name for each organization
    """
    name          = models.CharField( unique = True, max_length = 255 )

    def get_chapters(self):
        return Chapter.objects.filter(organization = self)

    def __unicode__(self):
        return self.name

class Chapter( models.Model ):
    """
    Base for each Organization chapter
    """
    name          = models.CharField( default = None, max_length = 255 )
    organization  = models.ForeignKey( Organization )
    organizer     = models.ForeignKey( User )

    logo          = models.URLField(            default = None, null = True )
    letter        = models.ForeignKey('Letter', default = None, null = True )
    website       = models.URLField(            default = None, null = True )

    def get_eventbrite(self):
        tickets = Eventbrite.objects.filter( chapter = self )
        return tickets

    def __unicode__(self):
        return self.name

class Eventbrite( models.Model ):
    chapter       = models.ForeignKey( Chapter )
    user_key      = models.CharField( default = None, max_length = 45 )
    organizer_id  = models.CharField( default = None, max_length = 45 )
    bot_email     = models.EmailField( default = None, null = True )

    def __unicode__(self):
        return self.chapter.name


class MeetUp( models.Model ):
    chapter    = models.ForeignKey( Chapter )
    member_id  = models.CharField( max_length = 45, default = None, null = True )
    token	   = models.CharField( max_length = 45, default = None, null = True )
    secret	   = models.CharField( max_length = 45, default = None, null = True )
    bot_email  = models.EmailField( default = None, null = True )

    def __unicode__(self):
        return self.chapter.name

class LeadBuyer( models.Model ):
    """
    Lead buyer interests
    """
    user            = models.ForeignKey( User )
    interests       = models.ManyToManyField( 'Interest' )

    def __unicode__(self):
        return user.email

class Interest(models.Model):
    """
    List of unique interests
    """
    interest        = models.CharField(unique = True, max_length = 255 )

    def __unicode__(self):
        return self.interest

class Deal(models.Model):
    """
    Deal is a link between an Interest and a Chapter. There should only be one
    deal for each Interest/Chapter pair
    """
    interest     = models.ForeignKey( Interest )
    chapter      = models.ForeignKey( Chapter )
    max_sell     = models.IntegerField(default = 1)

    def __unicode__(self):
        return self.interest.interest

# Term describes the terms for each Deal
class Term( models.Model ):
    """
    A Term are the terms of a Deal. There can be many Terms for each Deal
    """
    deal      = models.ForeignKey( Deal )
    canceled  = models.BooleanField(default = False)
    cost      = models.CharField( max_length = 10, blank = True, null = True )
    buyer     = models.ForeignKey( User, blank = True, null = True )

    # Check whether to execute this deal
    def execute(self, **kwargs):
        # If the subterm does not exist each one blows up
        try:
            return self.cancel.execute()
        except:
            pass
        try:
            return self.expire.execute()
        except:
            pass
        try:
            return self.count.execute(event = kwargs['event'])
        except:
            pass

        return False

    def __unicode__(self):
        return str(self.pk)

class Expire( Term ):
    """
    Subclass of Term that is good until an expiration date
    """
    date        = models.DateField()

    def execute(self, **kwargs):
        if self.buyer == None or self.canceled:
            return False
        # relativedelta(datetime1, datetime2)
        delta = self.date - date.today()
        if delta.days >= 0:
            return True
        return False

    def __unicode__(self, **kwargs):
        return '<Expire:'+ self.date.strftime("%Y-%m-%d") + '>'

class Cancel( Term ):
    """
    Subclass of Term that the Term is good until canceled
    """
    def execute(self, **kwargs):
        if self.buyer == None or self.canceled:
            return False
        return True

    def __unicode__(self):
        return '<Cancel>'

class Count( Term ):
    """
    Subclass of Term that is good for a specific number of Events
    """
    number       = models.IntegerField()
    remaining    = models.IntegerField()
    last_event   = models.ForeignKey('Event',  blank = True, null = True )

    def execute(self, **kwargs):
        if self.buyer == None or self.canceled:
            return False

        if self.last_event == None:
            self.last_event = kwargs['event']
            return True

        if self.last_event != kwargs['event']:
            if self.remaining > 0:
                self.last_event = kwargs['event']
                self.remaining -= 1
        return True


    def __unicode__(self):
        return '<Count:'+ str(self.number)+ '>'

class Connects(Term):
    """
    Subclass of Term that is good for a set number of connections
    """
    number      = models.IntegerField()
    remaining   = models.IntegerField()

    def execute(self, **kwargs):
        if self.buyer == None or self.canceled:
            return False

        if self.remaining > 0:
            self.remaining -= 1
            return True
        return False


class Letter( models.Model ):
    """
    Customized Email template letters to attendees and buyer Connections
    """
    letter      = models.FileField(upload_to = 'letters')

    def __unicode__(self):
        return self.letter

class EventManager(models.Manager):
    """
    Event class object manager
    """
    pass

class Event(models.Model):
    """
    Event description class
    """
    chapter      = models.ForeignKey( Chapter )
    event_id     = models.IntegerField( unique = True )
    describe     = models.TextField()
    date         = models.DateTimeField()
    attendees    = models.ManyToManyField(User, related_name = 'event_attendee')
    letter       = models.ForeignKey( Letter,  blank = True, null = True )
    objects      = EventManager()


    def get_deals( self, interest ):
        """
        Get deals for this event
        """

        # The interest may not be exactly the same, so check all
        for db_interest in Interest.objects.all( ):
            seq = SequenceMatcher( None, interest, db_interest.interest )

            # Found the closely matching interest, now find deals
            if round( seq.ratio(), 2 ) >= .90:
                try:
                    deals = Deal.objects.get( Q(chapter = self.chapter    ),
                                              Q(interest = db_interest    )
                                            )
                except Deal.DoesNotExist:
                    return []
                else:
                    return [deals]

        # If you are here no interests were found
        return []


    def add_connection( self, attendee, deal ):
        """
        Add a connection to an Event and an attendee
        """
        # Look for any existing deals
        try:
            connection  = Connection.objects.get( Q(event = self),
                                                  Q(deal  = deal),
                                                  Q(attendee = attendee)
                                                )
        # Not found, create a new one
        except Connection.DoesNotExist:
            connection = Connection( event     = self,
                                     deal     =  deal,
                                     attendee = attendee )
            connection.save()
            return True

        return False

    def __unicode__(self):
        return self.describe

class ConnectionManager(models.Manager):
    """
    Model Manager for Connection class
    """

    def for_user(self, user ):
        """
        Get Connections for a particular user
        """
        profile = user.get_profile()
        connections = []

        if profile.is_leadbuyer:
            terms = Term.objects.filter(buyer = user)
            for term in terms:
                deal = term
                for c in self.filter(deal = deal):
                    connections.append(c)

        if profile.is_attendee:
            for c in self.filter(attendee = user):
                connections.append(c)
        return connections

class Connection(models.Model):
    """
    Describes a connection for an Event, Deal, and attendee
    """
    event           = models.ForeignKey(Event)
    deal            = models.ForeignKey(Deal)
    attendee        = models.ForeignKey( User )
    date            = models.DateTimeField(auto_now = True)

    objects         = ConnectionManager()

    def get_buyers(self):
        """
        Who was the buyer of this Deal
        """
        buyers = []
        for term in self.deal.terms:
            if term.buyer != None:
                buyers.append(term.buyer)
        return buyers

    def is_connected(self, user ):
        """
        Returns whether a user is part of this connection
        """
        if self.attendee == user:
            return True
        terms = Term.objects.filter(buyer = user)
        if terms.count() > 0:
            return True

        return False

    def __unicode__(self):
        return self.attendee.email +' '+self.event.describe

"""
class Lead(models.Model):
    user            = models.ForeignKey(User)
    vendor_type     = models.CharField(max_length=100,  blank = True, null = True )
    budget          = models.CharField(max_length=100,  blank = True, null = True )
    timeframe       = models.CharField(max_length=100,  blank = True, null = True )
    published_date  = models.DateTimeField(auto_now = True)
    expires_date    = models.DateTimeField()
    description     = models.TextField()


    def __unicode__(self):
        return self.user.email +'-'+str(self.pk)
"""

