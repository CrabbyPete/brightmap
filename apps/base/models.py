from difflib                                import SequenceMatcher
from datetime                               import date

from django.db                              import models
from django.db.models                       import Q
from django.contrib.auth.models             import User
from django.contrib.localflavor.us.models   import PhoneNumberField
from django.contrib.contenttypes.models     import ContentType


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

    def chapters(self):
        return self.chapter_set.all()

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

    def deals( self ):
        # Get all the deals for this chapter
        return self.deal_set.all()

    def deal( self, interest ):
        # Get the deal for a specific interest
        return self.deal_set.get( interest = interest )

    def events( self ):
        # Get all the events for this chapter
        return self.event_set.all()

    def get_eventbrite( self ):
        # Get the Eventbrite ticket for this chapter
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

class InterestManager( models.Manager ):
    """
    Model manager for Interest
    """
    def close_to(self, interest, ratio = .90 ):
        # Return the closest interest in the database
        for i in self.all( ):
            seq = SequenceMatcher( None, interest, i.interest )
            if round( seq.ratio(), 2 ) >= ratio:
                return i
        return None

    def leads(self, event = None):
        # Return all the leads for this Interest
        interests = {}
        for survey in Survey.objects.all():
            if survey.interest == None:
                continue
            if survey.interest in interests:
                interests[survey.interest] += 1
            else:
                interests[survey.interest] = 1
        return interests


class Interest(models.Model):
    """
    List of unique interests
    """
    interest        = models.CharField( unique = True, max_length = 255 )
    occupation      = models.CharField( max_length = 255, default = None, null = True )
    objects         = InterestManager()

    def __unicode__(self):
        return self.interest

class Deal(models.Model):
    """
    Deal is a link between an Interest and a Chapter. There should only be one
    deal for each Interest/Chapter pair
    """
    interest     = models.ForeignKey( Interest )
    chapter      = models.ForeignKey( Chapter )
    max_sell     = models.IntegerField(default = 3)

    def connections(self):
        # Return all the connections for all Deals
        return self.connection_set.all()

    def terms(self):
        # Return all the Terms for this Deal
        return self.term_set.all()

    def __unicode__(self):
        return self.interest.interest

# Term describes the terms for each Deal
class Term( models.Model ):
    """
    A Term are the terms of a Deal. There can be many Terms for each Deal
    """

    deal      = models.ForeignKey( Deal )
    canceled  = models.BooleanField( default = False )
    cost      = models.CharField( max_length = 10, blank = True, null = True )
    buyer     = models.ForeignKey( User, blank = True, null = True )

    def get_child(self):
        for related in self._meta.get_all_related_objects():
            try:
                return getattr(self, related.get_accessor_name())
            except:
                pass
        return None

    def execute(self, **kwargs):
        term = self.get_child()
        return term.execute()


class Expire( Term ):
    """
    Subclass of Term that is good until an expiration date
    """
    date        = models.DateField()

    def execute(self, **kwargs):
        if self.buyer == None or self.canceled:
            return False

        delta = self.date - date.today()
        if delta.days >= 0:
            return True
        return False

    def __unicode__(self, **kwargs):
        return 'expire:'+ self.date.strftime("%Y-%m-%d")

class Cancel( Term ):
    """
    Subclass of Term that the Term is good until canceled
    """
    def execute(self, **kwargs):
        # Has this Term been canceled
        if self.buyer == None or self.canceled:
            return False
        return True

    def __unicode__(self):
        return 'cancel'

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
        return 'count:'+ str(self.number)

class Connects( Term ):
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

    def __unicode__(self):
        return 'connects:'+ str(self.number)

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
    letter       = models.ForeignKey( Letter,  blank = True, null = True )
    objects      = EventManager()


    def surveys(self):
        return self.survey_set.all()

    def connections(self):
        return self.connection_set.all()

    def attendees(self, attendee = None):
        # Return attendess for this event. If attendee is None return all

        if attendee:
            return self.survey_set.filter(attendee = attendee)

        # Return all attendees for this event
        attendees = {}
        for survey in self.survey_set.all():
            if not survey.attendee in attendees.keys():
                if survey.interest != None:
                    attendees[survey.attendee] = 1
                else:
                    attendees[survey.attendee] = 0
            else:
                attendees[survey.attendee] += 1

        return attendees

    def interests(self, open = False ):
        """
        Return the interests for this event, and the number of each
        If attendee return interests for the attendee otherwise return all
        """
        interests = {}
        for survey in self.survey_set.all():

            # Ignore None
            if survey.interest == None:
                continue

            # Just return open deals
            if open:
                # Only exclude those connected with an exclusive deal : max_deal = 1
                try:
                    deal = self.chapter.deal( survey.interest )
                except Deal.DoesNotExist:
                    pass
                else:
                    if deal.max_sell == 1:
                        continue

            if not survey.interest.interest in interests:
                interests[survey.interest.interest] = 1
            else:
                interests[survey.interest.interest] += 1
        return interests

    def connections(self):
        connections = []
        for survey in self.survey_set.all():
            if not survey.interest:
                continue
            for c in Connection.objects.filter(survey = survey):
                connections.append(c)
        return connections


    def deals( self, interest ):
        """
        Get deals for a normalized interest for this event
        """
        deal_list = []
        normal_interest = Interest.objects.close_to( interest )
        deals = Deal.objects.filter( chapter  = self.chapter,
                                     interest = normal_interest
                                   )
        for deal in deals:
            for event in deal.chapter.events():
                if event == self:
                    deal_list.append(deal)

        return deal_list


    def add_connection( self, survey, deal ):
        """
        Add a connection to an Event and an attendee
        """
        # Look for any existing deals
        try:
            connection  = Connection.objects.get( survey = survey,
                                                  deal   = deal
                                                 )
            # Not found, create a new one
        except Connection.DoesNotExist:
            connection = Connection( survey = survey, deal = deal )
            connection.save()
            return True

        return False

    def __unicode__(self):
        return self.describe

class SurveyManager(models.Manager):
    pass


class Survey(models.Model):
    event       = models.ForeignKey( Event )
    attendee    = models.ForeignKey( User )
    interest    = models.ForeignKey( Interest, default = None, null = True )
    mailed      = models.IntegerField( default = 0 )

    def connections(self):
        return self.connection_set.all()

    def mails_for(self):
        total_mails = 0
        mails = Survey.objects.filter( event    = self.event,
                                       attendee = self.attendee )
        for mail in mails:
            total_mails += mail.mailed
        return total_mails


    def __unicode__(self):
        name = self.attendee.email+':'+ self.event.describe
        if self.interest != None:
            name += '(' + self.interest.interest + ')'
        return name

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
                for c in self.filter(deal = term.deal):
                    connections.append(c)

        if profile.is_attendee:
            surveys = Survey.objects.filter( attendee = user )
            for survey in surveys:
                for c in self.filter( survey = survey ):
                    connections.append(c)

        return connections

    def for_event(self, event ):
        """
        Get all Connections for an event
        """
        self.filter(event.survey)

class Connection(models.Model):
    """
    Describes a connection for an Event, Deal, and attendee
    """
    survey          = models.ForeignKey( Survey )
    deal            = models.ForeignKey( Deal )
    date            = models.DateTimeField( auto_now = True )

    objects         = ConnectionManager()

    def buyers(self):
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
        terms = Term.objects.filter( buyer = user )
        if terms.count() > 0:
            return True

        return False

    def __unicode__(self):
        return self.survey.attendee.email + '-' + self.deal.interest.interest

