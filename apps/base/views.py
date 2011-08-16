# Python imports
import settings

from dateutil.parser import *

# Django imports
from django.contrib                 import  auth
from django.http                    import  HttpResponseRedirect
from django.forms.util              import  ErrorList
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext
from django.views.decorators.csrf   import  csrf_protect, csrf_exempt
from django.db.models               import  Q
from django.contrib.auth.models     import  User
from django.core.urlresolvers       import  reverse

# Local imports
from models                         import *
from forms                          import *


# Homepage
def homepage( request ):
    if request.user.is_authenticated():
        return welcome(request)

    return login(request)

# Login in users, if registered bring the to their page
@csrf_protect
def welcome( request ):

    def submit_form( ):
        c = {}
        return render_to_response('welcome.html', c, context_instance=RequestContext(request))

    if request.method == 'GET':
        return submit_form()

@csrf_protect
def login(request):

    def submit_form(form):
        c = {'form':form}
        return render_to_response('index.html', c, context_instance=RequestContext(request))

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
        user = User.objects.get(Q(username = username))
    except User.DoesNotExist:
        try:
            user = User.objects.get(Q(email = username))
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

# Sign up for an account
@csrf_protect
def signup(request):

    def submit_form(form):
        c = {'form':form }
        return render_to_response('signup.html', c, context_instance=RequestContext(request))

    #GET
    if request.method == 'GET':
        return submit_form(SignUpForm())

    # POST
    form = SignUpForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Check password input
    password = form.cleaned_data['password']
    pass_confirm = form.cleaned_data['pass_confirm']
    if password != pass_confirm:
        form._errors['password'] = ErrorList(['The passwords do not match'])
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
        username = email[0:30]
        user  = User.objects.create_user( username = username,
                                          email = email,
                                          password=password
                                        )
    except Exception,e:
        print e
        form._errors['username'] = ErrorList(['This name has already been used'])
        return submit_form(form)

    user.first_name = form.cleaned_data['first_name'].capitalize()
    user.last_name =  form.cleaned_data['last_name'].capitalize()

    user.save()

    # Create the profile
    profile  = Profile(user = user)
    if form.cleaned_data['is_organizer']:
        profile.is_organizer = True

    if form.cleaned_data['is_leadbuyer']:
        profile.is_leadbuyer = True

    if 'phone' in form.cleaned_data:
        profile.phone = form.cleaned_data['phone']

    if 'address' in form.cleaned_data['address']:
        profile.address = address

    profile.save()

    # Login the new user
    user = auth.authenticate(username=user.username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)

    return HttpResponseRedirect('/')

@csrf_protect
def  edit_profile(request):
    def submit_form(form):
        c = {'form':form }
        return render_to_response('edit_profile.html', c, context_instance=RequestContext(request))

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
    try:
        user.save()
        profile.save()
    except:
        pass

    return HttpResponseRedirect('/')

# Log out a user
@csrf_protect
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

@csrf_protect
def show_chapter(request):

    def submit_form(organizations):
        c = {'organizations':organizations}
        return render_to_response( 'show_chapter.html', c,
                                   context_instance=RequestContext(request) )
    # GET: All organizations
    organizations = Organization.objects.all()
    return submit_form(organizations)

@csrf_protect
def edit_chapter( request ):

    def submit_form(form):
        c = {'form':form}
        return render_to_response( 'edit_chapter.html', c,
                                   context_instance=RequestContext(request) )

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

    def submit_form(form):
        c = {'form':form }
        return render_to_response( 'edit_interest.html', c,
                                   context_instance=RequestContext(request) )
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
            in_interest = Interest.objects.get( Q(interest = interest) )
        except Interest.DoesNotExist:
            in_interest = Interest( interest = interest )
            in_interest.save()

    return HttpResponseRedirect('/')

# Show details of a single event
def show_event(request):

    def submit_form(event, attendees ):
        c = { 'event'      :event,
              'attendees'  :attendees,
            }

        return render_to_response( 'show_event.html', c,
                                   context_instance=RequestContext(request) )

   # GET: All the attendees for a given event
    if request.method == 'GET' and 'event' in request.GET:
        event = Event.objects.get(pk = request.GET['event'])
        attendees   = event.attendees()
        return submit_form(event, attendees )


# List the users current events
def show_events(request):

    def submit_form(events):
        c = {'events':events }
        return render_to_response( 'show_events.html', c,
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

 # Create a new
def edit_deal(request):

    def submit_form(form, terms):
        c = {'form': form, 'terms':terms }
        return render_to_response( 'edit_deal.html', c,
                                   context_instance=RequestContext(request) )
    #GET
    if request.method == 'GET':
        # Edit an existing deal
        if 'deal' in request.GET:
            deal = Deal.objects.get(pk = request.GET['deal'])
            data = {
                    'interest' :deal.interest,
                    'organizer':deal.chapter.pk,
                    'max_sell' :deal.max_sell
            }
            form = DealForm(initial = data)
            terms = TermForm()

            return submit_form(form,terms)

        # Create a new deal
        elif'organizer' in request.GET:
            form = DealForm( initial={'organizer':request.GET['organizer']} )
            terms = TermForm()
            return submit_form(form, terms)
        else:
            #Log an error
            pass

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


    deal.max_sell = form.cleaned_data['max_sell']
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

    def submit_form(deals):
        c = { 'deals':deals }
        return render_to_response( 'show_deals.html', c,
                                   context_instance=RequestContext(request) )

    if request.method == 'GET':
        if 'chapter' in request.GET:
            deals = Deal.objects.filter(chapter=request.GET['chapter'])
        else:
            deals = Deal.objects.all()

        return submit_form(deals)

def show_deal(request):

    def submit_form( deal ):
        c = {'deal':deal }
        return render_to_response( 'show_deal.html', c,
                                   context_instance=RequestContext(request) )

    if request.method == 'GET' and 'deal' in request.GET:
        deal = Deal.objects.get(pk = request.GET['deal'])
        return submit_form(deal)

def cancel_term(request):
    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        term.canceled = True
        term.save()
        return HttpResponseRedirect(reverse('show_deals'))


def show_buyer(request):
    def submit_form(buyers,connections = None):
        c = {'buyers':buyers,
             'connections':connections}
        return render_to_response( 'show_buyer.html', c,
                                   context_instance=RequestContext(request) )

    if request.method == 'GET':
        if 'buyer' in request.GET:
            if request.GET['buyer'] == 'all':
                buyers = Profile.objects.filter(is_leadbuyer = True)
                return submit_form( buyers )
            else:
                buyer  = User.objects.get(pk = request.GET['buyer'])
                connections = Connection.objects.for_user(buyer)
                return submit_form([buyer], connections)


    if request.method == 'POST':
        if 'buyer' in request.POST:
            terms = Terms.objects.filter()
            return HttpResponseRedirect('/')

def edit_buyer(request):
    def submit_form(form):
        c = {'form':form }
        return render_to_response( 'edit_buyer.html', c,
                                   context_instance=RequestContext(request) )
    # GET
    if request.method == 'GET':
        if 'buyer' in request.GET:

                user = User.objects.get(pk = request.GET['buyer'])
                buyers = [user.get_profile]

        return submit_form(BuyerForm())

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

    def submit_form( form ):
        c = {'form':form }
        return render_to_response( 'add_buyer.html', c,
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


def show_connection(request):
    def submit_form( connections ):
        c = {'connections':connections }
        return render_to_response( 'show_connection.html', c,
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
    def submit_form(form):
        c = {'form':form }
        return render_to_response( 'edit_letter.html', c,
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


