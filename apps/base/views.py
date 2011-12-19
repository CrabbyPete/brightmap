# Python imports
import logging
logger = logging.getLogger(__name__)

# Django imports
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.http                    import  HttpResponseRedirect
from django.forms.util              import  ErrorList
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext
from django.views.decorators.csrf   import  csrf_protect
from django.core.urlresolvers       import  reverse
from django.core.exceptions         import  ObjectDoesNotExist
from django.views.generic.edit      import  FormView
from django.template                import  loader, Context
from django.core.mail               import  EmailMultiAlternatives


# Local imports
from passw                          import generate
from models                         import ( Event, Chapter,  Profile, LeadBuyer, 
                                             Deal,  Survey,   Invoice, Connection,
                                             Term,  Interest,  
                                           )
                                        

from forms                          import ( LoginForm,       DealForm,
                                             LeadBuyerForm,   ChapterForm, 
                                             EventbriteForm,  EventForm, 
                                             SurveyForm,      ConnectionForm, 
                                             UserProfileForm, UserForm,       
                                             TermForm,        InvoiceForm,
                                             InterestForm
                                           )


from settings                       import SEND_EMAIL

# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes

# Import accounting functions
from cron.accounting                import invoice_user, bill_user, notify_user


def homepage( request ):
    # Homepage
    if request.user.is_authenticated():
        return welcome(request)

    #return login(request)
    return render_to_response('indexR.html', {'login':LoginForm()}, context_instance=RequestContext(request))

@csrf_protect
def welcome( request ):
    # Check if they are a Lead Buyer, and make sure they have a valid profile
    user = request.user

    # Get the profile, Admin may not have a profile yet
    try:
        profile = user.get_profile()
    except ObjectDoesNotExist:
        if user.is_staff or user.is_superuser:
            profile = Profile( user = user )
            profile.save()

    if user.is_staff or user.is_superuser:
            return render_to_response('welcome.html', {}, context_instance=RequestContext(request))
    
    if profile.is_leadbuyer:
        if not profile.is_ready:
            return HttpResponseRedirect( reverse('lb_payment') )
        else:
            return HttpResponseRedirect( reverse('lb_dash') )
        
    return HttpResponseRedirect( reverse('or_signup') )

def learn(request):
    if request.method == 'GET':
        if 'organizer' in request.GET:
            return render_to_response( 'learn_more_organizers.html', 
                                       {'login':LoginForm()}, 
                                       context_instance=RequestContext(request)
                                     )
        if 'service' in request.GET:
            return render_to_response( 'learn_more_providers.html', 
                                       {'login':LoginForm()}, 
                                       context_instance=RequestContext(request)
                                     )
        return welcome(request)


def forgot( request, username ):

    try:
        user = User.objects.get(email = username)
    except User.DoesNotExist:
        user = None
        password = None
 
    else:
        password = generate(6)
        user.set_password(password)
        user.save()
    
    # Set up the context
    c = Context({ 'user':user, 'password' :password })

    # Render the message and log it
    template = loader.get_template('letters/forgot.tmpl')
    message = template.render(c)

    subject = 'BrightMap Account'
    bcc = [ 'bcc@brightmap.com' ]
    from_email = '<admin@brightmap.com>'

    to_email = [ '%s %s <%s>'% ( user.first_name, user.last_name, user.email ) ]
    if SEND_EMAIL:
        to_email = [ '%s %s <%s>'% ( user.first_name, user.last_name, user.email ) ]
    else:
        #TESTING BELOW REMOVE LATER
        to_email = ['Pete Douma <pete.douma@gmail.com>']

    # Send the email
    msg = EmailMultiAlternatives( subject    = subject,
                                  body       = message,
                                  from_email = from_email,
                                  to         = to_email,
                                  bcc        = bcc
                                )

    try:
        msg.send( fail_silently = False )
    except:
        pass
 
    return HttpResponseRedirect('/')

    
@csrf_protect
def login(request):
    # Login users

    def submit_form(form):
        c = {'login':form}
        return render_to_response('indexR.html', c, context_instance=RequestContext(request))

    if request.method == 'GET':
        form = LoginForm()
        return submit_form(form)

    form = LoginForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Get the name and password and login
    username = form.cleaned_data['username']
    password = form.cleaned_data['password']

    if form.cleaned_data['forgot']:
        return forgot(request, username)
    
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




def community(request):
    return render_to_response('community.html', {},
                               context_instance=RequestContext(request))
def about(request):
    return render_to_response('about.html', {},
                               context_instance=RequestContext(request))
    
def terms(request):
    return render_to_response('terms.html', {},
                               context_instance=RequestContext(request))
    
@csrf_protect
def logout(request):
    # Log out a user
    auth.logout(request)
    return HttpResponseRedirect('/')



"""
    All Admin functions are here
""" 

class ProfileView( FormView ):
    template_name    = 'admin/profile.html'
    form_class       = UserProfileForm
 
    def get(self, request, *args, **kwargs):
        if 'user' in request.GET:
            user = User.objects.get(pk = request.GET['user'])
            profile = Profile.objects.get( user = user )
            
            uform = UserForm(instance = user)
            pform = UserProfileForm( instance = profile )
            
            return self.render_to_response( {'uform':uform, 'pform':pform} )
        
        return HttpResponseRedirect('/')   
   
    def form_valid(self, form):
        return HttpResponseRedirect('/')         


class InterestView( FormView ):
    """ View, edit, and create new Interests """
    
    template_name   = 'admin/interest.html'
    form_class      = InterestForm
    
    def get(self, request, *args, **kwargs):
        if 'interest' in self.request.GET:
            if self.request.GET['interest'] == 'new':
                interest = None
                form = InterestForm()
            else:
                interest = Interest.objects.get( pk = self.request.GET['interest'] )
                form = InterestForm( instance = interest )
            return self.render_to_response( {'form':form, 'interest':interest} )
        
        else:
            interests = Interest.objects.all().order_by('interest')
            return self.render_to_response( {'interests':interests} )

 
    def form_valid(self, form):
        """ Edit or create a new Interest """
        name = form.cleaned_data['interest']
        if self.request.GET['interest']:
            interest = Interest.objects.get( pk = self.request.GET['interest'] )
        else:
            # Each interest must be unique. The form overrides unique_validate, so make sure 
            try:
                interest = Interest.objects.get( interest = name )
            except Interest.DoesNotExist:
                interest = Interest( interest = name )
        
        interest.status = form.cleaned_data['status']
        interest.save()
        
        return HttpResponseRedirect(reverse('interest'))

class ChapterView( FormView ):
    template_name    = 'admin/chapter.html'
    form_class       = ChapterForm

    def get(self, request, *args, **kwargs):
        if 'chapter' in request.GET:
            if self.request.GET['chapter'] == 'new':
                form = ChapterForm()
            else:
                chapter = Chapter.objects.get( pk = self.request.GET['chapter'] )
                form = ChapterForm( instance = chapter )
            return self.render_to_response( {'form':form, 'chapter':chapter} )
            
        else:
            chapters = Chapter.objects.all()
            return self.render_to_response( {'chapters':chapters} )

 
    def form_valid(self, form):
        if 'chapter' in self.request.GET:
            if self.request.GET['chapter']:
                chapter = Chapter.objects.get( pk = self.request.GET['chapter'] )
            
                organization  = form.cleaned_data['organization']
                organizer     = form.cleaned_data['organizer']
                logo          = form.cleaned_data['logo']
                letter        = form.cleaned_data['letter']
                website       = form.cleaned_data['website']
                
                chapter.letter = letter
                chapter.website = website
                chapter.logo    = logo
                
                chapter.save()
        
        return HttpResponseRedirect(reverse('chapter'))

class EventbriteView( FormView ):
    template_name   = 'admin/eventbrite.html'
    form_class      = EventbriteForm
    
    def get(self, request, *args, **kwargs):
        if 'chapter' in request.GET:
            chapter = Chapter.objects.get( pk = self.request.GET['chapter'] )
            eventbrite = chapter.get_eventbrite()
            if len(eventbrite) > 0:
                form = EventbriteForm( instance = eventbrite[0] )
            else:
                form = EventbriteForm({'chapter':chapter})
            return self.render_to_response( {'form':form, 'chapter':chapter} )
            
  
    def form_valid(self, form ):
        return HttpResponseRedirect('/')
    
class DealView( FormView ):
    template_name   = 'admin/deal.html'
    form_class      = DealForm
    
    def get(self, request, *args, **kwargs):
        if 'deal' in request.GET:
            if request.GET['deal'] == 'new':
                form = DealForm()
                deal = None
            else: 
                deal = Deal.objects.get(pk = request.GET['deal'])
                form = DealForm( instance = deal )
            return self.render_to_response( {'form': form, 'deal':deal} )
        
        if 'chapter' in request.GET:
            chapter = Chapter.objects.get(pk = request.GET['chapter'])
            deals = chapter.deals()
   
        elif 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            deals = leadbuyer.deals()
            
 
            
        return self.render_to_response( {'deals':deals} )
            
    def form_valid(self, form ):
        if 'interest' in form.cleaned_data:
            interest = form.cleaned_data['interest']
        
        return HttpResponseRedirect(reverse('deal'))

class TermView( FormView ):
    template_name   = 'admin/term.html'
    form_class      = TermForm
    
    def get(self, request, *args, **kwargs):
        if 'deal' in request.GET:
            deal = Deal.objects.get(pk = request.GET['deal'])
            terms = deal.terms()
            return self.render_to_response( {'terms':terms} )
        
        
        
        if 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            terms = leadbuyer.deals()
            return self.render_to_response( {'terms':terms} )
    
        if 'term' in request.GET:
            term = Term.objects.get(pk = request.GET['term'])
        
        form = TermForm (instance = term )
        return self.render_to_response( {'form':form, 'term':term} )
            
        return HttpResponseRedirect('/')
            
    def form_valid(self, form ):
        if 'term' in self.request.GET:           
            term = Term.objects.get( pk = self.request.GET['term'] )
            if form.cleaned_data['status']:
                term.status = form.cleaned_data['status']
            
            if form.cleaned_data['cost']:
                term.cost = form.cleaned_data['cost']
            
            term.save()
                                     
        return HttpResponseRedirect(reverse('term')+'?leadbuyer='+str(term.buyer.pk) )
        
class LeadBuyerView( FormView ):
    template_name   = 'admin/leadbuyer.html'
    form_class      = LeadBuyerForm
    
    def get(self, request, *args, **kwargs):
        if 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            form = LeadBuyerForm( instance = leadbuyer )
            return self.render_to_response( {'form': form, 'leadbuyer':leadbuyer} )
        else:
            leadbuyers = LeadBuyer.objects.all().order_by('user__last_name')
            return self.render_to_response( {'leadbuyers': leadbuyers} )
 
    
    def form_valid(self, form):
        return HttpResponseRedirect('/')


class EventView( FormView ):
    template_name   = 'admin/event.html'
    form_class      = EventForm
    
    def get(self, request, *args, **kwargs):
        if 'event' in request.GET:
            event = Event.objects.get(pk = request.GET['event'])
            form = EventForm(instance = event )
            return self.render_to_response( {'form':form, 'event': event} )
        
        if 'chapter' in request.GET:
            chapter = Chapter.objects.get(pk = request.GET['chapter'])
            events = chapter.events()
            return self.render_to_response( {'events': events} )

    
    def form_valid(self, form):
        return HttpResponseRedirect('/')
    
    
class SurveyView( FormView ):
    template_name   = 'admin/survey.html'
    form_class      = SurveyForm
    
    def get(self, request, *args, **kwargs):
        if 'event' in request.GET:
            event = Event.objects.get(pk = request.GET['event'])
            surveys = event.surveys( lead = True )
            return self.render_to_response( {'surveys': surveys} )
        
        if 'survey' in request.GET:
            survey = Survey.objects.get(pk = request.GET['survey'])
            form = SurveyForm( instance = survey)
            return self.render_to_response( {'form':form, 'survey': survey} )
    
    def form_valid(self, form):
        return HttpResponseRedirect('/')


class ConnectionView( FormView ):
    template_name   = 'admin/connection.html'
    form_class      = ConnectionForm
    
    def get(self, request, *args, **kwargs):
        if 'connection' in request.GET:
            connection = Connection.objects.get(pk = request.GET['connection'])
            form = ConnectionForm( instance = connection)
            return self.render_to_response( {'form':form, 'connection': connection} )
        
        if 'event' in request.GET:
            event = Event.objects.get(pk = request.GET['event'])
            connections = event.connections()
  
        elif 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            connections = leadbuyer.connections()
        
        return self.render_to_response( {'connections': connections} )
            
    
    def form_valid(self, form):
        connection = Connection.objects.get(pk = self.request.GET['connection'] )
        status = form.cleaned_data['status']
        connection.status = status
        connection.save()        
        return HttpResponseRedirect(reverse('invoice'))



class InvoiceView ( FormView):
    template_name   = 'admin/invoice.html'
    form_class      = InvoiceForm
    
    def get(self, request, *args, **kwargs):
        if 'invoice' in request.GET:
            invoice = Invoice.objects.get(pk = request.GET['invoice'])
           
            # Update to the latest invoice
            invoice = invoice_user ( invoice.user, invoice.first_day, invoice.last_day )

            form = InvoiceForm(instance = invoice)
            connections = invoice.connections()
            return self.render_to_response( {'form':form, 'invoice':invoice, 'connections':connections} )
        
        invoices = Invoice.objects.all().order_by('issued')
        return self.render_to_response( {'invoices':invoices} )
        
 
            
    def form_valid(self, form ):
        invoice = Invoice.objects.get( pk = self.request.GET['invoice'] )
        invoice = bill_user ( invoice )
        if invoice.status == 'paid':
            notify_user( invoice )
        invoice.save()
        
        
        return HttpResponseRedirect(reverse('invoice'))

