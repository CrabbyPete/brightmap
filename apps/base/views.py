# Python imports

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


# Local imports
from models                         import Event, Chapter, Profile, LeadBuyer, Deal
                                        

from forms                          import ( LoginForm,     InterestForm,   DealForm,
                                             LeadBuyerForm, ProfileForm,    ChapterForm, 
                                             LetterForm,    EventbriteForm, EventForm, 
                                             SurveyForm,    ConnectionForm, TermForm
                                           )

from social.models                  import LinkedInProfile

def homepage( request ):
    # Homepage
    if request.user.is_authenticated():
        return welcome(request)

    #return login(request)
    return render_to_response('index.html', {'login':LoginForm()}, context_instance=RequestContext(request))

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

    if user.is_staff or user.is_super_user:
            return render_to_response('welcome.html', {}, context_instance=RequestContext(request))
    
    if profile.is_leadbuyer:
        if not profile.is_ready:
            return HttpResponseRedirect( reverse('lb_payment') )
        else:
            return HttpResponseRedirect( reverse('lb_dash') )
        
        return HttpResponseRedirect( reverse('or_signup') )

@csrf_protect
def login(request):
    # Login users

    def submit_form(form):
        c = {'login':form}
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
        return HttpResponseRedirect('/')

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
            deal = Deal.objects.get(pk = request.GET['deal'])
            form = DealForm( instance = deal )
            return self.render_to_response( {'form': form} )
        
        if 'chapter' in request.GET:
            chapter = Chapter.objects.get(pk = request.GET['chapter'])
            deals = chapter.deals()
   
        elif 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            deals = leadbuyer.deals()
            
        return self.render_to_response( {'deals':deals} )
            
    def form_valid(self, form ):
        return HttpResponseRedirect('/')

class TermView( FormView ):
    template_name   = 'admin/term.html'
    form_class      = TermForm
    
    def get(self, request, *args, **kwargs):
        if 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            terms = leadbuyer.deals()
            
        return self.render_to_response( {'terms':terms} )
            
    def form_valid(self, form ):
        return HttpResponseRedirect('/')
        
class LeadBuyerView( FormView ):
    template_name   = 'admin/leadbuyer.html'
    form_class      = LeadBuyerForm
    
    def get(self, request, *args, **kwargs):
        if 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            form = LeadBuyerForm( instance = leadbuyer )
            return self.render_to_response( {'form': form, 'leadbuyer':leadbuyer} )
        else:
            leadbuyers = LeadBuyer.objects.all()
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
    
    def form_valid(self, form):
        return HttpResponseRedirect('/')


class ConnectionView( FormView ):
    template_name   = 'admin/connection.html'
    form_class      = ConnectionForm
    
    def get(self, request, *args, **kwargs):
        if 'event' in request.GET:
            event = Event.objects.get(pk = request.GET['event'])
            connections = event.connections()
  
        elif 'leadbuyer' in request.GET:
            leadbuyer = LeadBuyer.objects.get(pk = request.GET['leadbuyer'])
            connections = leadbuyer.connections()
        
        return self.render_to_response( {'connections': connections} )
            
    
    def form_valid(self, form):
        return HttpResponseRedirect('/')

