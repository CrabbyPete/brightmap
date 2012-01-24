
from difflib                                import SequenceMatcher
from datetime                               import datetime, date, time, timedelta

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

    is_ready      = models.BooleanField( default = False )
    is_active     = models.BooleanField( default = True  )
    is_organizer  = models.BooleanField( default = False )
    is_leadbuyer  = models.BooleanField( default = False )
    is_attendee   = models.BooleanField( default = False )
    is_agreed     = models.BooleanField( default = False )

    newsletter    = models.BooleanField( default = True )
        
    def __unicode__(self):
        return self.user.email

class Authorize( models.Model ):
    user            = models.ForeignKey( User )

    customer_id     = models.CharField( max_length = 255 )
    profile_id      = models.CharField( max_length = 255 )
    payment_profile = models.CharField( max_length = 255 )
    

    def __unicode__(self):
        return self.user.last_name+','+self.user.first_name


class Invoice( models.Model ):
    user        = models.ForeignKey( User )
    title       = models.CharField( max_length = 255, blank = True, null = True )

    cost        = models.DecimalField( max_digits = 10, decimal_places = 2, default = 0.00 )
    issued      = models.DateTimeField( auto_now_add = True )

    first_day   = models.DateField()
    last_day    = models.DateField()
    
    status      = models.CharField( max_length = 20, default ='issued' )
 
    def authorized(self):
        try:
            Authorize.objects.get( user = self.user )
            return True
        except Authorize.DoesNotExist:
            return False
        
    def connections(self):
        return Connection.objects.for_buyer(self.user,[self.first_day, self.last_day])
    
    def commissions(self):
        return self.commission_set.all()
    
    def bill(self):
        return self.issued.strftime('%B %Y')
        
    def __unicode__(self):
        return self.user.email +'-'+self.title


class Commission( models.Model ):
    invoice     = models.ForeignKey( 'Invoice' )
    chapter     = models.ForeignKey( 'Chapter' )   
    cost        = models.DecimalField( max_digits = 10, decimal_places = 2, default = 0.00 )
    issued      = models.DateTimeField( auto_now_add = True )    
    status      = models.CharField( max_length = 20, default ='pending' )

    def __unicode__(self):
        return self.chapter.name +':'+self.invoice


class Organization( models.Model ):
    """
    Base name for each organization
    """
    name          = models.CharField( unique = True, max_length = 255 )

    def chapters(self):
        return self.chapter_set.all()

    def __unicode__(self):
        return self.name

class ChapterManager(models.Manager):

    def for_user(self, user ):
        return self.filter( organizer = user )


class Chapter( models.Model ):
    """
    Base for each Organization chapter
    """
    name          = models.CharField( default = None, max_length = 255 )
    organization  = models.ForeignKey( Organization, default = None, blank = True, null = True )
    organizer     = models.ForeignKey( User )
    paypal        = models.CharField( default = None, null = True,  max_length = 255 )

    logo          = models.URLField(            default = None, null = True )
    letter        = models.ForeignKey('Letter', default = None, null = True )
    website       = models.URLField(            default = None, null = True )
    objects       = ChapterManager() 
    

    def deals( self ):
        # Get all the deals for this chapter
        return self.deal_set.all()

    def deal( self, interest ):
        # Get the deal for a specific interest
        try:
            return self.deal_set.get( interest = interest )
        except:
            return None

    def configured(self):
        ticket = self.eventbrite_set.get()
        if ticket.user_key and ticket.organizer_id:
            return True
        return False
    
    
    def sponsors(self):
        sponsors = []
        deals = Deal.objects.filter ( chapter = self )
        for deal in deals:
            terms = Term.objects.filter( deal = deal, 
                                         exclusive = True, 
                                         cost = 0, 
                                         status = 'approved' )
            sponsors.extend(terms)
        return sponsors

    def events( self ):
        # Get all the events for this chapter
        return self.event_set.all()

    def get_eventbrite( self ):
        # Get the Eventbrite ticket for this chapter
        try:
            tickets = Eventbrite.objects.get( chapter = self )
        except:
            return None
        return tickets


    def buyers( self ):
        # Get all the buyers for this chapters events
        buyers = []
        deals = self.deals()
        for deal in deals:
            for term in deal.terms():
                if term.status == 'approved':
                    buyers.append(term.buyer)
        return buyers

    def __unicode__(self):
        return self.name

class Eventbrite( models.Model ):
    """
    Information needed to access Eventbrite API
    """
    chapter       = models.ForeignKey( Chapter )
    user_key      = models.CharField(  blank = True, null = True, max_length = 45 )
    organizer_id  = models.CharField(  blank = True, null = True, max_length = 45 )
    bot_email     = models.EmailField( blank = True, null = True, max_length = 255 )

    def __unicode__(self):
        return self.chapter.name


class MeetUp( models.Model ):
    """
    Information needed to access Meetup API
    """
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
    user        = models.ForeignKey( User )
    letter      = models.ForeignKey( 'Letter',  blank = True, null = True )

    budget      = models.DecimalField( max_digits= 12,
                                       decimal_places = 2,
                                       blank = True, null = True
                                     )

    def authorized(self):
        try:
            Authorize.objects.get(user = self.user )
            return True
        except Authorize.DoesNotExist:
            return False
        
    def deals(self):
        return Term.objects.filter(buyer = self.user)

    def connections(self):
        return Connection.objects.for_buyer(self.user)

    def __unicode__(self):
        return self.user.email

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
        # Return all Interests and a count for all Interest
        interests = {}
        for survey in Survey.objects.all():
            if survey.interest == None:
                continue
            if survey.interest in interests:
                interests[survey.interest] += 1
            else:
                interests[survey.interest] = 1
        return interests


INTEREST_STATUS = ((0,'standard' ),
                   (1,'extend'   ),
                   (2,'custom'   ),
                  )
class Interest(models.Model):
    """
    List of unique interests
    """
    interest        = models.CharField( unique = True, max_length = 255 )
    occupation      = models.CharField( max_length = 255, default = None, null = True )
    objects         = InterestManager()
    status          = models.CharField( max_length = 20, default = 'standard' )

    def __unicode__(self):
        return self.interest

    def events(self, day = None, open = False ):
        """
        Return all the events that have this interest
        """
        report = {}
        if day == None:
            day = datetime.today()

        query = Survey.objects.filter( interest = self,
                                       event__date__gte = day )
        for survey in query:
            
            # Check is exclusive, if there is a deal and its exclusive, ignore
            if open:
                deal = survey.event.chapter.deal( self )
                if deal and deal.exclusive():
                    continue

            # Count
            if survey.event in report:
                report[survey.event] += 1
            else:
                report[survey.event] = 1

        return report

class Deal(models.Model):
    """
    Deal is a link between an Interest and a Chapter. There should only be one
    deal for each Interest/Chapter pair
    """
    interest     = models.ForeignKey( Interest )
    chapter      = models.ForeignKey( Chapter )

    def connections(self):
        # Return all the connections for all Deals
        return self.connection_set.all()

    def terms(self):
        # Return all the Terms for this Deal
        return self.term_set.all()

    def active(self):
        return Term.objects.filter(deal = self, status = 'approved')
    
    
    def exclusive ( self ):
        # Return the excluve for this deal, None if none
        # Make sure exclusive don't allow other terms
        for term in self.terms():
            if term.exclusive and term.status == 'approved':
                return term
        return None

    def __unicode__(self):
        return self.chapter.name +':' + self.interest.interest

TERM_STATUS = ('canceled', 'pending', 'approved', 'rejected', 'sponsored')

class Term( models.Model ):
    """
    A Term are the terms of a Deal. There can be many Terms for each Deal
    """
    deal      = models.ForeignKey( Deal )
    cost      = models.DecimalField( max_digits = 10,
                                     decimal_places = 2,
                                     default = 0.00
                                    )
    buyer     = models.ForeignKey( User, blank = True, null = True )
    exclusive = models.BooleanField( default = False )
    status    = models.CharField( max_length = 20, default ='pending' )
    modified  = models.DateTimeField( auto_now = True )
    """
    Valid Status:
        pending   - a lead buyer wants this deal, but not approved
        approved  - this deal approved by the organizer
        rejected  - this deal rejected
        canceled  - this deal canceled
    """
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

    def __unicode__(self):
        return self.buyer.email +'-' +\
               self.deal.chapter.name +':' + self.deal.interest.interest

    def owner(self):
        return self.deal.chapter.organizer
        
    def connections( self, dates = None ):
        if dates:
            return Connection.objects.filter( term = self, date__range = dates )
        else:
            return Connection.objects.filter( term = self )

    def total( self, dates = None ):
        connections = self.connections( dates )
        price = self.cost * len(connections)
        return price

    
    def this_month(self):
        first = datetime.today().replace(day = 1)
        if first.month == 12:
            last = first.replace(day = 31)
        else:
            last  = first.replace (month = first.month + 1 ) - timedelta( days = 1 )
        return (first,last)
    
    def monthly_connections( self ):
        return self.connections( self.this_month() )

    def monthly_total(self):
        return self.total( self.this_month() )

    def canceled(self):
        self.status = 'canceled'
        self.save()
        
class Expire( Term ):
    """
    Subclass of Term that is good until an expiration date
    """
    date        = models.DateField()

    def execute(self, **kwargs):
        if self.buyer == None or self.status != 'approved':
            return False

        if self.date >= date.today():
            return True
        else:
            self.canceled()
            return False
        
        self.canceled()
        return False

    def __unicode__(self, **kwargs):
        return 'expire:'+ self.date.strftime("%Y-%m-%d")

class Cancel( Term ):
    """
    Subclass of Term that the Term is good until canceled
    """
    def execute(self, **kwargs):
        # Has this Term been canceled
        if self.buyer == None or self.status != 'approved':
            return False

        return True

    def __unicode__(self):
        return 'cancel'

class Budget( Term ):

    remaining   = models.DecimalField( max_digits= 12,
                                       decimal_places = 2,
                                       blank = True,
                                       null = True
                                     )
    def execute(self, **kwargs):
        # Has this Term been canceled
        if self.buyer == None or self.status != 'approved':
            return False

        # Refill on day 1
        today = date.today()
        if today.day == 1:
            self.remaining = self.buyer.budget

        # Is money left to do this?
        if self.remaining < self.cost:
            return False

        # Deduct the money and do it.
        self.remaining -= self.cost
        self.save()
        return True

class Count( Term ):
    """
    Subclass of Term that is good for a specific number of Events
    """
    number       = models.IntegerField()
    remaining    = models.IntegerField()
    last_event   = models.ForeignKey('Event',  blank = True, null = True )

    def execute(self, **kwargs):
        if self.buyer == None or self.status != 'approved':
            return False

        if self.last_event == None:
            self.last_event = kwargs['event']
            return True

        if self.last_event != kwargs['event']:
            if self.remaining > 0:
                self.last_event = kwargs['event']
                self.remaining -= 1
                self.save()
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
        if self.buyer == None or self.status != 'approved':
            return False

        if self.remaining <= 0:
            return False

        self.remaining -= 1
        self.save()
        return True


    def __unicode__(self):
        return 'connects:'+ str(self.number)


class Letter( models.Model ):
    """
    Customized Email template letters to attendees and buyer Connections
    """
    letter      = models.FileField(upload_to = 'letters')
    name        = models.CharField(max_length = 255, default = None, null = True )

    def __unicode__(self):
        return self.name


class EventManager(models.Manager):
    """
    Event class object manager
    """
    def planned(self):
        """
        Return future events
        """
        today = datetime.today()
        events = self.filter( date__gte = today )
        return events

class Event(models.Model):
    """
    Event description class
    """
    chapter      = models.ForeignKey( Chapter )
    event_id     = models.BigIntegerField( unique = True )
    describe     = models.TextField()
    date         = models.DateTimeField()
    letter       = models.ForeignKey( Letter,  blank = True, null = True )
    objects      = EventManager()


    def surveys(self, lead = False ):
        if not lead:
            return self.survey_set.all()
        else:
            return self.survey_set.exclude( interest = None )
        

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

        # Return a dictionary of attendees and number of Interests
        return attendees

    
    def interests(self, opn = False ):
        """
        Return the interests for this event, and the number of each
        If attendee return interests for the attendee otherwise return all
        """
        interests = {}
        for survey in self.survey_set.exclude( interest = None ):

            # Just return open deals
            if opn:
                # Only exclude those connected with an exclusive deal
                try:
                    deal = self.chapter.deal( survey.interest )
                except Deal.DoesNotExist:
                    pass
                else:
                    # There are no deals or the deal has an exclusive
                    if deal == None or deal.exclusive() != None:
                        continue

            if not survey.interest.interest in interests:
                interests[survey.interest.interest] = 1
            else:
                interests[survey.interest.interest] += 1
        return interests
    
    def connections(self):
        #return self.connection_set.all()
        conns = []
        for survey in self.surveys(lead = True):
            for c in Connection.objects.filter(survey = survey):
                conns.append(c)
        return conns
    

    def deals( self, interest ):
        """
        Get deals for a normalized interest for this event
        """
        normal_interest = Interest.objects.close_to( interest )
        deals = Deal.objects.filter( chapter  = self.chapter,
                                     interest = normal_interest
                                   )
        return deals


    def add_connection( self, survey, term ):
        # Add a connection to an Event and an attendee

        # Look for any existing deals
        try:
            connection  = Connection.objects.get( survey = survey,
                                                  term   = term
                                                 )
            # Not found, create a new one
        except Connection.DoesNotExist:
            connection = Connection( survey = survey,
                                     term   = term
                                   )
            connection.save()
            return connection

        return False

    def __unicode__(self):
        return self.describe

class SurveyManager(models.Manager):
    pass


class Survey(models.Model):
    """
    Information for each survey filled out for an event by an attendee
    """
    event       = models.ForeignKey( Event )
    attendee    = models.ForeignKey( User )
    interest    = models.ForeignKey( Interest, default = None, null = True )
    mailed      = models.IntegerField( default = 0 )

    def connections(self):
        return self.connection_set.all()

    def mails_for(self):
        """
        Emails sent for an attendee, per event
        """
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
    def for_buyer(self, user, dates = None ):
        """
        Only return buyer connections
        """
        # Only for lead buyers
        if  not user.get_profile().is_leadbuyer:
            return []
        
        # Dates is a set, but if date instance, change to datetime instance, make sure it max and min
        if dates:
            dates = ( datetime.combine( dates[0], time.min ),  datetime.combine( dates[1], time.max ) )
        
        # Get all the connections
        connections = []
        for term in Term.objects.filter(buyer = user):
            if dates:
                connection = self.filter( term = term, date__range = dates )
            else:
                connection = self.filter( term = term )
            connections.extend(connection)
        
        return connections
        
 
class Connection(models.Model):
    """
    Describes a connection for an Event, Deal, and attendee
    """
    survey      = models.ForeignKey( Survey )
    term        = models.ForeignKey( Term )
    date        = models.DateTimeField( auto_now_add = True )
    status      = models.CharField( max_length = 20, default ='sent' )

    objects     = ConnectionManager()

    def buyers(self):
        return self.term.buyer


    def is_connected(self, user ):
        #Returns whether a user is part of this connection
        terms = Term.objects.filter( buyer = user )
        if terms.count() > 0:
            return True

        return False

    def __unicode__(self):
        return self.survey.attendee.email + '-' +\
               self.term.buyer.email + ':' +\
               self.survey.event.describe
