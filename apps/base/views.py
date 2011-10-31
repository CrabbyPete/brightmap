# Python imports
import settings
import logging

from datetime                       import datetime
from dateutils                      import relativedelta

# Django imports
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.http                    import  HttpResponseRedirect
from django.forms.util              import  ErrorList
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext, Context, loader
from django.views.decorators.csrf   import  csrf_protect, csrf_exempt
from django.core.urlresolvers       import  reverse
from django.core.exceptions         import  ObjectDoesNotExist
from django.core.mail               import  send_mail, EmailMultiAlternatives


# Local imports
from models                         import *
from forms                          import *
from passw                          import gen
from social.models                  import *

def homepage( request ):
    # Homepage
    if request.user.is_authenticated():
        return welcome(request)

    #return login(request)
    return render_to_response('index.html', {}, context_instance=RequestContext(request))

@csrf_protect
def welcome( request ):
    # Check if they are a Lead Buyer, and make sure they have a valid profile
    user = request.user

    # Get the profile, Admin may not have a profile yet
    try:
        profile = user.get_profile()
    except ObjectDoesNotExist:
        if user.is_staff or user.is_super_user:
            profile = Profile( user = user )
            profile.save()

    if profile.is_leadbuyer:
        if not profile.is_ready:
            return HttpResponseRedirect( reverse('lb_payment') )
        else:
            return HttpResponseRedirect( reverse('lb_dash') )

    return render_to_response('welcome.html', {}, context_instance=RequestContext(request))


@csrf_protect
def login(request):
    # Login users

    def submit_form(form):
        c = {'form':form}
        return render_to_response('login.html', c, context_instance=RequestContext(request))

    if request.method == 'GET':
        form = LoginForm()
        return submit_form(form)

    form = LoginForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Get the name and password and login
    username = form.cleaned_data['username']
    password = form.cleaned_data['password']

    try:
        user = User.objects.get(username = username)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email = username)
        except User.DoesNotExist:
            form._errors['username']  = ErrorList(["User does not exist or wrong password"])
            return submit_form(form)

    # Once you have them authenticate
    user = auth.authenticate(username=user.username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)

        # Show User Page
        return HttpResponseRedirect('/')
    else:
        form._errors['username']  = ErrorList(["User does not exist or wrong password"])
        return submit_form(form)


@csrf_protect
def signup(request):
    # Sign up for an account

    def submit_form(form):
        c = {'form':form }
        return render_to_response('signup.html', c, context_instance=RequestContext(request))

    #GET
    if request.method == 'GET':
        return submit_form(BuyerForm())

    # POST
    form = BuyerForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Get the email address and see if they are in the database
    email          = form.cleaned_data['email']
    email_verify   = form.cleaned_data['email_verify']
    if email != email_verify:
        form._errors['email'] = ErrorList(["The emails do not match"])
        return submit_form(form)
    
    # Check the passwords match
    password     = form.cleaned_data['password']
    pass_confirm = form.cleaned_data['pass_confirm']
    if password != pass_confirm:
        form._errors['password'] = ErrorList(["The passwords do not match"])
        return submit_form(form)

    # Make sure they agree
    if not form.cleaned_data['agree']:
        form._errors['agree'] = ErrorList(["Please check agreement"])
        return submit_form(form)
    
    try:
        user = User.objects.get(email = email)
        profile = user.get_profile()

    except User.DoesNotExist:
        username = email[0:30]
        user  = User.objects.create_user( username = username,
                                          email = email,
                                          password = password
                                         )
        
        user.first_name = form.cleaned_data['first_name'].capitalize()
        user.last_name  = form.cleaned_data['last_name'].capitalize()

        user.save()
        profile = Profile( user = user)
    else:
        if not user.check_password(password) and profile.is_ready:
            form._errors['password'] = ErrorList(["User exist with a different password"])
            return submit_form(form)
        else:
            user.set_password(password)
            user.save()
            
    profile.is_leadbuyer = True
    profile.is_agreed    = True
      
    if 'phone' in form.cleaned_data:
        profile.phone = form.cleaned_data['phone']

    if 'address' in form.cleaned_data:
        profile.address = form.cleaned_data['address']
    
    if 'company' in form.cleaned_data:
        profile.company = form.cleaned_data['company']
        
    if 'title' in form.cleaned_data:
        profile.title = form.cleaned_data['title']
        
    if 'website' in form.cleaned_data:
        profile.website = form.cleaned_data['website']
    
    if 'twitter' in form.cleaned_data:
        profile.twitter = form.cleaned_data['twitter']
    
    if 'linkedin' in form.cleaned_data:
        profile.linkedin = form.cleaned_data['linkedin']
    
    profile.save()
    
    # Check if there is a leadbuyer record for this user
    if profile.is_leadbuyer:
        try:
             leadb = LeadBuyer.objects.get(user = user)
        except LeadBuyer.DoesNotExist:
            leadb = LeadBuyer(user = user)
            leadb.save()

    # Login the new user
    user = auth.authenticate(username=user.username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)

    return HttpResponseRedirect(reverse('lb_payment'))

    # Email the new user their password
    """
    url = settings.SITE_BASE + reverse('login')
    c = Context({'password' :password,
                 'user'     :user,
                 'url'      :url
                })

    # Render the letter
    template = loader.get_template('letters/signup.tmpl')
    message = template.render(c)

    subject = "Welcome to BrightMap"
    recipients = [ user.email ]

    msg = EmailMultiAlternatives( subject,
                                  message,
                                  'welcome@brightmap.com',
                                  recipients
                                )
    try:
        msg.send( fail_silently = False )
    except:
        err = "Email Send Error For: " + event.chapter.organizer.email
        logger.error("Email Send Error:")

    return render_to_response('thanks.html', {},
                               context_instance=RequestContext(request))
    """

def community(request):
    return render_to_response('community.html', {},
                               context_instance=RequestContext(request))

@csrf_protect
def logout(request):
    # Log out a user
    auth.logout(request)
    return HttpResponseRedirect('/')

"""
    All Admin functions are here
"""
@csrf_protect
def  edit_profile(request):
    # Edit a users profile

    def submit_form(form, lead = None):
        return render_to_response( 'admin/edit_profile.html',
                                   {'form':form, 'lead':lead } ,
                                   context_instance=RequestContext(request)
                                 )

   # Need to know what user this is
    user    = request.user
    profile = user.get_profile()
    default_password ='3dhl4df6ajhhd9ir'

    # GET: Here for the first time, show the currents values
    if request.method == 'GET':

        # Set up a default password, to see if the user tried to change passwords
        data = {'email'         :user.email,
                'password'      :default_password,
                'pass_confirm'  :default_password,
                'phone'         :profile.phone,
                'first_name'    :user.first_name,
                'last_name'     :user.last_name,
                'address'       :profile.address,
                'company'       :profile.company,
                'title'         :profile.title,
                'website'       :profile.website,
                'is_organizer'  :profile.is_organizer,
                'is_leadbuyer'  :profile.is_leadbuyer,
                'is_attendee'   :profile.is_attendee,
                'newsletter'    :profile.newsletter
                }

        form = ProfileForm(data)
        if profile.is_leadbuyer:
            lead = LeadBuyerForm()
            return submit_form(form,lead)
        else:
            return submit_form(form)

    #POST: Get the form data and change the values
    form = ProfileForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Check password input
    password = form.cleaned_data['password']
    pass_confirm = form.cleaned_data['pass_confirm']
    if password != default_password:
        if password != pass_confirm:
            form._errors['password'] = ErrorList(["The passwords do not match"])
            return submit_form(form)
        else:
            user.set_password(password)

    phone  = form.cleaned_data['phone']
    profile.phone = phone.replace('-','')

    # Confirm email
    user.email           = form.cleaned_data['email']
    user.first_name      = form.cleaned_data['first_name']
    user.last_name       = form.cleaned_data['last_name']
    profile.title        = form.cleaned_data['title']
    profile.company      = form.cleaned_data['company']
    profile.website      = form.cleaned_data['website']
    profile.is_organizer = form.cleaned_data['is_organizer']
    profile.is_leadbuyer = form.cleaned_data['is_leadbuyer']
    profile.is_attendee  = form.cleaned_data['is_attendee']

    profile.newsletter   = form.cleaned_data['newsletter']
    profile.address      = form.cleaned_data['address']
    """
    elif address != '':
        local = geocode(address)
        if 'address' in local:
            profile.address = local['address']
        else:
            profile.address = address
    """
    profile.is_ready     = True
    try:
        user.save()
        profile.save()
    except:
        pass

    return HttpResponseRedirect('/')



@csrf_protect
def show_chapter(request):
    # Show Chapter details

    def submit_form(organizations):
        return render_to_response( 'admin/show_chapter.html',
                                   {'organizations':organizations},
                                   context_instance=RequestContext(request)
                                 )

    # GET: All organizations
    if 'organizer' in request.GET:
        return submit_form(Organization.objects.all())

    organizations = []
    for chapter in Chapter.objects.filter(organizer = request.user):
        organizations.append(chapter.organization)

    return submit_form(organizations)

@csrf_protect
def edit_chapter( request ):
    # Edit Chapter details

    def submit_form(form):
        return render_to_response( 'admin/edit_chapter.html',
                                   {'form':form},
                                   context_instance=RequestContext(request)
                                 )

    # GET: Edit a chapter or create a new one
    if request.method == 'GET':
        if 'chapter' in request.GET:
            chapter = Chapter.objects.get(pk = request.GET['chapter'])
            form = ChapterForm( instance = chapter )
            return submit_form(form)
        else:
            return submit_form(ChapterForm())

    # POST: Change the requested chapter or create it
    form = ChapterForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    user_key        = form.cleaned_data['user_key']
    organizer_id    = form.cleaned_data['organizer_id']
    organization    = form.cleaned_data['organization']

    # Edit an existing chapter
    try:
        organizer = Organizer.objects.get(organizer_id = organizer_id)

    # Create a new one
    except Organizer.DoesNotExist:
        organizer = Organizer( user         = request.user,
                               user_key     = user_key,
                               organizer_id = organizer_id,
                               organization = organization
                             )
    else:
        organizer.user_key = user_key
        organizer.organization = organization

    organizer.save()

    return HttpResponseRedirect('/')

@csrf_protect
def edit_interest( request ):
    # Edit Interest

    def submit_form(form):
        return render_to_response( 'admin/edit_interest.html',
                                   {'form':form },
                                   context_instance=RequestContext(request)
                                 )
    # GET: All the current interests
    if request.method == 'GET':
        interests = Interest.objects.all()
        interest_str = ''
        for interest in interests:
            interest_str += interest.interest+'\r\n'

        form = InterestForm( {'interests':interest_str} )
        return submit_form(form)

    # POST: Check out each to see if any are new
    form = InterestForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    interests = form.cleaned_data['interests']
    interests = interests.split('\r\n')
    for interest in interests:
        try:
            in_interest = Interest.objects.get( interest = interest )
        except Interest.DoesNotExist:
            in_interest = Interest( interest = interest )
            in_interest.save()

    return HttpResponseRedirect('/')


def show_event(request):
    # Show details of a single event
    def submit_form(event, attendees ):
        return render_to_response( 'admin/show_event.html',
                                   { 'event':event, 'attendees':attendees },
                                   context_instance=RequestContext(request) )

   # GET: All the attendees for a given event
    if request.method == 'GET' and 'event' in request.GET:
        event = Event.objects.get(pk = request.GET['event'])
        attendees   = event.attendees()
        return submit_form(event, attendees )

def show_events(request):
    # List the users current events
    def submit_form(events):
        return render_to_response( 'admin/show_events.html',
                                   {'events':events },
                                   context_instance=RequestContext(request) )

    # GET: All events or events for a specific chapter
    if request.method == 'GET':
        if 'chapter' in request.GET:

            # All or specific organizers?
            if request.GET['chapter'] == 'all':
                events = Event.objects.all()
            else:
                chapter = Chapter.objects.get(pk = request.GET['chapter'])
                events  = chapter.events()
            return submit_form(events)


def edit_deal(request):
    # Create or edit a Deal

    def submit_form( form ):
        return render_to_response( 'admin/edit_deal.html',
                                   {'form': form },
                                   context_instance=RequestContext(request) )
    #GET
    if request.method == 'GET':

        # Edit an existing deal
        if 'term' in request.GET:
            term = Term.objects.get(pk = request.GET['term'])
            data = {
                    'interest' :term.deal.interest,
                    'organizer':term.deal.chapter.pk,
                    'cost':term.cost,
                    'buyer':term.buyer
            }
            form = DealForm(initial = data)
            return submit_form(form)

        # Create a new deal
        elif'organizer' in request.GET:
            form = DealForm( initial={'organizer':request.GET['organizer']} )
            return submit_form(form)

        # Apply to a new deal
        else:
            form = DealForm()
            return submit_form(form)

    # POST:
    form = DealForm(request.POST)
    terms = TermForm(request.POST)

    if not form.is_valid():
        return submit_form(form, terms)

    add_terms = form.cleaned_data['add_terms']

    organizer = Organizer.objects.get(pk = form.cleaned_data['organizer'])
    if 'delete' in form.cleaned_data:
        pass

    interest  = Interest.objects.get(interest = form.cleaned_data['interest'])

    # Check if the deal exist already
    try:
        deal = Deal.objects.get( interest = interest,
                                 organizer = organizer )
    except Deal.DoesNotExist:
        deal = Deal( interest = interest,
                     organizer = organizer )

    deal.save()

    if not add_terms:
        return HttpResponseRedirect(reverse('show_organizer'))

    # Add terms added
    # Try and clean the terms form
    try:
        if not terms.is_valid():
            return submit_form(form, terms)

    except ValueError, e:
        print e

    cost      = int(form.data['cost'])

    # If nothing selected you will not get a terms_0
    if not u'terms_0' in form.data:
        terms.errors['terms'] = "A term selection is required"
        return submit_form(form,terms)

    # Get which term was selected from terms_0
    term_type = form.data['terms_0']
    if term_type == 'Cancel':
            term = Cancel(cost = cost)
    elif term_type == 'Count':
        count = int(form.data['terms_3'])
        term = Count(cost = cost, number = count, remaining = count)
    else:
        date = form.data['terms_2']
        date = parse(date)
        term = Expire(cost = cost, date = date )

    # See if a buyer was added
    if 'buyer' in form.data and form.data['buyers'] != None:
        try:
            buyer = User.objects.get(email = form.data['buyers'])
            term.buyer = buyer
        except:
            pass

    # Save the term and add it to the deal
    term.save()
    deal.terms.add(term)

    deal.save()
    return HttpResponseRedirect(reverse('show_organizer'))

def show_deals(request):
    # Show a list of Deals

    def submit_form(deals):
        return render_to_response( 'admin/show_deals.html',
                                   { 'deals':deals },
                                   context_instance=RequestContext(request)
                                 )

    if request.method == 'GET':
        if 'open' in request.GET:
            open = request.GET['open']

        if 'chapter' in request.GET:
            chapter = Chapter.objects.get( pk = request.GET['chapter'])
            deals = chapter.deals()
        else:
            deals = Deal.objects.all()

        return submit_form(deals)

def show_deal(request):
    # Show specific details for a Deal

    def submit_form( deal ):
        return render_to_response( 'admin/show_deal.html',
                                   {'deal':deal },
                                   context_instance=RequestContext(request) )

    if request.method == 'GET' and 'deal' in request.GET:
        deal = Deal.objects.get(pk = request.GET['deal'])
        return submit_form(deal)

def cancel_term(request):
    # Cancel Terms of a Deal

    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        term.canceled = True
        term.save()
        return HttpResponseRedirect(reverse('show_deals'))

def show_buyers(request):
    pass

def show_buyer(request):
    # Show LeadBuyer details

    def submit_form( buyer ):
        return render_to_response( 'admin/show_buyer.html',
                                   {'buyer':buyer },
                                   context_instance=RequestContext(request) )

    if request.method == 'GET':
        if 'buyer' in request.GET:
            if request.GET['buyer'] == 'all':
                buyers = Profile.objects.filter(is_leadbuyer = True)
                return render_to_response( 'admin/show_buyers.html',
                                           {'buyers':buyers},
                                     context_instance=RequestContext(request) )


            else:
                profile = Profile.objects.get(pk = request.GET['buyer'])
                try:
                    buyer  = LeadBuyer.objects.get(user = profile.user)
                except LeadBuyer.DoesNotExist:
                    buyer = LeadBuyer( user = request.user)
                    buyer.save()
        else:
            try:
                buyer  = LeadBuyer.objects.get(user = request.user)

            except LeadBuyer.DoesNotExist:
                buyer = LeadBuyer( user = request.user)
                buyer.save()

        return submit_form(buyer)


    if request.method == 'POST':
            return HttpResponseRedirect('/')

@csrf_protect
def edit_buyer(request):
    # Edit LeadBuyer details

    def submit_form(form):
        return render_to_response( 'admin/edit_buyer.html',
                                   {'form':form },
                                   context_instance=RequestContext(request) )
    # GET
    if request.method == 'GET':
        if 'buyer' in request.GET:
            user = User.objects.get(pk = request.GET['buyer'])
            buyer = user.get_profile
        else:
            user = request.user
            buyer = user.get_profile()

        # Check if they have a LinkedIn profile
        try:
            linkedin = LinkedInProfile.objects.get(user = user)
        except LinkedInProfile.DoesNotExist:
            data = {
                    'phone':        buyer.phone,
                    'title':        buyer.title,
                    'company':      buyer.company,
                    'address':      buyer.address,
                    'website':      buyer.website
                    }
        else:
            data = {
                    'phone':        buyer.phone,
                    'title':        linkedin.title,
                    'company':      linkedin.company,
                    'address':      buyer.address,
                    'website':      buyer.website
                    }

        form = BuyerForm(data)
        return submit_form(form)

    # POST
    form = BuyerForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Get the email address and double check it to make sure its unique
    email = form.cleaned_data['email']
    if email != u'':
        qry = User.objects.filter(email = email)
        if qry.count() >= 1:
            form.errors['email'] = "This email is in use"
            return submit_form(form)

    # Create the user
    try:
        password = 'new_user'
        user  = User.objects.create_user(username=email, email = email, password=password)
    except Exception,e:
        print e
        form._errors['email'] = ErrorList(['This email has already been used'])
        return submit_form(form)

    user.first_name = form.cleaned_data['first_name']
    user.last_name = form.cleaned_data['last_name']

    user.save()

    profile  = Profile(user = user)
    profile.is_leadbuyer = True

    profile.phone   = form.cleaned_data['phone']
    profile.address = form.cleaned_data['address']
    profile.company = form.cleaned_data['company']
    profile.website = form.cleaned_data['website']
    profile.save()

    return HttpResponseRedirect('/')

def add_buyer(request):
    # Add a LeadBuyer

    def submit_form( form ):
        return render_to_response( 'admin/add_buyer.html',
                                   {'form':form },
                                   context_instance=RequestContext(request) )

    if request.method == 'GET':
        if 'term' in request.GET:
            data = {'term':  request.GET['term'] }
            form = BuyersForm(data)
            return submit_form(form)

    if request.method == 'POST':
        form = BuyersForm(request.POST)
        if not form.is_valid():
            return submit_form(form)

        term  = Term.objects.get(pk = form.cleaned_data['term'])
        buyer = User.objects.get(email = form.cleaned_data['buyers'])
        term.buyer = buyer
        term.save()

        return HttpResponseRedirect('/')

def show_survey(request):
    # Show what surveys were answered

    def submit_form( surveys ):
        return render_to_response( 'admin/show_survey.html',
                                   {'surveys':surveys },
                                    context_instance=RequestContext(request) )
    if 'event' in request.GET:
        event = Event.objects.get( pk = request.GET['event'] )

        if 'open' in request.GET:
            open = request.GET['open']
        else:
            open = True

        surveys = []
        for survey in event.surveys():
            if survey.interest == None:
                continue

            connects = survey.connections()
            if open and connects.count() > 0:
                continue
            surveys.append( survey )
        return submit_form( surveys )

    return HttpResponseRedirect('/')

def show_connection(request):
    # Show details of a Connections

    def submit_form( connections ):
        return render_to_response( 'admin/show_connection.html',
                                   {'connections':connections },
                                    context_instance=RequestContext(request) )

    if request.method == 'GET':
        if 'connection' in request.GET:
            # All or specific organizers?
            if request.GET['connection'] == 'all':
                connections = Connection.objects.filter()
                return submit_form(connections)
            else:
                connections = Connection.objects.get(pk=request.GET['connection'])
                return submit_form([connections])

        elif 'chapter' in request.GET:
            connections = []
            events = Event.objects.filter(chapter = request.GET['chapter'])
            for event in events:
                for c in event.connections():
                    connections.append(c)
            return submit_form(connections)

        elif 'user' in request.GET:
            user  = User.objects.get(pk = request.GET['user'])
            connections = Connection.objects.for_user(user)
            return submit_form(connections)

    return HttpResponseRedirect('/')

# Edit/Upload an Email template
@csrf_protect
def edit_letter(request):
    # Edit the current Chapter Letter

    def submit_form(form):
        return render_to_response( 'admin/edit_letter.html',
                                   {'form':form },
                                   context_instance=RequestContext(request) )
    if request.method == 'GET':
        if 'organizer' in request.GET:
            organizer = request.GET['organizer']

        return submit_form(LetterForm())

    form = LetterForm( request.POST, request.FILES )
    if not form.is_valid():
        return submit_form(form)

    # Who owns this file
    organizer = form.cleaned_data['organizer']

    # Upload the file
    # Note: make sure the file name is unique
    file = request.FILES['letter']
    file_to_open = settings.MEDIA_ROOT+'//letters//'+ organizer.organization + '.tmp'
    fd = open(file_to_open, 'wb+')
    if file.multiple_chunks():
        for chunk in file.chunks():
            fd.write(chunk)
    else:
        fd.write(file.read())
    fd.close()

    # Save a record in the database
    letter = Letter( organizer = organizer, letter = file_to_open )

    letter.save()
    return HttpResponseRedirect('/')

@csrf_protect
def show_available_deals(request):
    """
    Report number of interests for each event
    """
    def submit_form( form, interest = None, report = None ):
        return render_to_response( 'admin/show_available_deals.html',
                                    { 'form':form,
                                      'interest': interest,
                                      'report':report
                                    },
                                    context_instance=RequestContext(request)
                                 )

    # GET
    if request.method == 'GET':
        form = InterestForm()
        return submit_form(form)

    # POST Return a dictionary of events and interests
    form = InterestForm(request.POST)
    if not form.is_valid():
            return submit_form(form)

    interest = form.cleaned_data['interests']
    interest = Interest.objects.get( interest = interest )
    report = interest.events( open = True )
    return submit_form( form, interest, report )


def buy_deal(request):

    def submit_form(form):
        return render_to_response( 'admin/buy_deal.html',
                                   {'form':form },
                                   context_instance=RequestContext(request) )
    # GET
    if request.method == 'GET':
        if 'event' in request.GET and 'interest' in request.GET:
            event = Event.objects.get(pk = request.GET['event'])
            chapter = event.chapter
            interest = Interest.objects.get(interest = request.GET['interest'])

        data = { 'chapter':chapter,
                 'interest':interest.interest
               }
        form = BuyDealForm(data)
        return submit_form(form)

    # POST
    if request.method == 'POST':
        form = BuyDealForm(request.POST)
        if not form.is_valid():
            return submit_form(form)

        chapter   = form.cleaned_data['chapter']
        interest  = form.cleaned_data['interest']
        deal_type = form.cleaned_data['deal_type']

        # Check if there are any existing deals
        interest = Interest.objects.get(interest = interest)
        chapter  = Chapter.objects.get(name = chapter)
        try:
            deal = Deal.objects.get( chapter = chapter, interest = interest )

        # If not create one
        except Deal.DoesNotExist:
            deal = Deal( chapter = chapter, interest = interest )
            deal.save()

        # Check the type of deal
        if deal_type == 'Trial':
            one_month = datetime.now() + relativedelta(months=+1)
            expire = Expire( deal = deal,
                             date = one_month,
                             cost = 0,
                             status = 'pending',
                             buyer = request.user
                            )
            expire.save()
        else:
            if deal_type == 'Exclusive':
                cost = 50.00
                exclusive = True
            elif deal_type ==  'Nonexclusive':
                cost = 20.00
                exclusive = False

            cancel = Cancel( deal = deal,
                             cost = cost,
                             exclusive = exclusive,
                             buyer = request.user
                            )
            cancel.save()
    return HttpResponseRedirect('/')

