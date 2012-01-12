# Python imports
from datetime                       import date, datetime
import  logging
logger = logging.getLogger('organizer')

# Django imports
from django.views.generic.edit      import  FormView
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.forms.util              import  ErrorList
from django.core.urlresolvers       import  reverse
from django.http                    import  HttpResponseRedirect
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext
from django.contrib.auth.decorators import  login_required

#Local imports
from base.mail                      import Mail
from base.models                    import ( Profile,       Organization,   Chapter, 
                                             Interest,      Deal,           Event,
                                             Eventbrite,    Term,           TERM_STATUS
                                            )
from forms                          import OrganizerForm, CategoryForm


class SignUpView( FormView ):
    template_name = 'organ/signup.html'
    form_class    = OrganizerForm
    password      ='2434&)%*%%^$#@' 
    
    def get_initial( self ):
        if self.request.method == 'GET':
 
            if 'chapter' in self.request.GET:
                chapter = Chapter.objects.get(pk = self.request.GET['chapter'])
                chapter_name = chapter.name
            else:
                chapter = ""
                chapter_name = None
            
            if self.request.user.is_authenticated():
                
                user = self.request.user
                profile = user.get_profile()
                
                self.initial = dict ( email         = user.email,
                                      email_verify  = user.email,
                                      first_name    = user.first_name,
                                      last_name     = user.last_name,
                                      password      = self.password,
                                      pass_confirm  = self.password,
                                      chapter       = chapter_name,
                                      pay_pal       = chapter.paypal,
                                      agree         = profile.is_agreed
                                    )
        else:
            self.initial = {}
        
        return self.initial

   
    def form_valid( self, form ):
        """
        Process the validated Event Organizer signup page
        """
    
        # Get the email address and see if they are in the database
        email   = form.cleaned_data['email']
        
        # Get paypal info
        pay_pal = form.cleaned_data['pay_pal']
        """
        email_verify   = form.cleaned_data['email_verify']
        if email != email_verify:
            form._errors['email'] = ErrorList(["The emails do not match"])
            return self.form_invalid(form)
        """
        
        # Check the passwords match
        password     = form.cleaned_data['password']
        pass_confirm = form.cleaned_data['pass_confirm']
        
        if password != self.password:
            if  password != pass_confirm:
                form._errors['password'] = ErrorList(["The passwords do not match"])
                return self.form_invalid(form)

        # Make sure they agree
        if not form.cleaned_data['agree']:
            form._errors['agree'] = ErrorList(["Please check agreement"])
            return self.form_invalid(form)
    
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
            profile.save()
        
        else:
            user.first_name = form.cleaned_data['first_name'].capitalize()
            user.last_name  = form.cleaned_data['last_name'].capitalize()

            if password != self.password:
                user.set_password(password)
            
            user.save()
            
        profile.is_agreed    = True
        profile.save()
  
        # See if the organization and chapter exist
        
        """ Take this out for now. One organizer, chapter per user 
        name = form.cleaned_data['chapter']
     
        try:
            organization = Organization.objects.get( name = name, organizer =  )
        except Organization.DoesNotExist:
            organization = Organization( name = name )
            organization.save()
        """
        # See if the chapter exists. If its blank its the same as the organization name
        name = form.cleaned_data['chapter']
        if name == '':
            chapters = Chapter.objects.for_user( user = user )
            
            # Take the first one now
            if len( chapters) >= 1:
                chapter = chapters[0]
            else:
                # If the used did not give a chapter and none exist
                form._errors['chapter'] = ErrorList(["Please provide a chapter name"])
                return self.form_invalid(form)
        else:           
            try:
                chapter = Chapter.objects.get( name = name, organizer = user )
        
            except Chapter.DoesNotExist:
                
                # If this is the first time here create a chapter
                if not profile.is_organizer:
                    """ Temporarily one organizer per chapter """
                    organization = Organization( name = name )
                    organization.save()
                    
                    chapter = Chapter( name = name, 
                                       organizer = user,
                                       organization = organization,
                                       paypal = pay_pal )
                    chapter.save()
            
                    # Create an Eventbrite record for them 
                    eventbrite = Eventbrite( chapter = chapter )
                    eventbrite.save()
                
                # Otherwise this is a rename
                else:
                    chapters = Chapter.objects.for_user(user)
                    chapter = chapters[0]
                    
        chapter.name = name
        chapter.paypal = pay_pal
        chapter.save()
                    
        # Login the new user
        user = auth.authenticate(username=user.username, password=password)
        if user is not None and user.is_active:
            auth.login(self.request, user)
            
        
        # If you had a profile 
        if profile.is_organizer:
            return HttpResponseRedirect ( reverse('or_dash')+"?state=profile" )
        else: 
            profile.is_organizer = True
            profile.save()
            return HttpResponseRedirect( reverse('or_category')+'?chapter='+str(chapter.id) )
        
class CategoryView( FormView ):
    template_name = 'organ/or_category.html'
    form_class    = CategoryForm
    
    def get_initial( self ):
        if self.request.method == 'GET':
            if 'chapter' in self.request.GET:
                chapter = self.request.GET['chapter']
                return dict ( chapter = chapter )


    def form_valid( self, form ):
        interests  = form.cleaned_data['standard']
        interests.extend( form.cleaned_data['other'] )
 
        # Check the custom field
        if form.cleaned_data['custom']:
            if not form.cleaned_data['field']:
                form._errors['field'] = ErrorList(["What is the custom field"])
                return self.form_invalid(form)
            interests.append(form.cleaned_data['field'])
        
        # Make sure no more than 6 choices        
        if len(interests) > 6:
            form._errors['standard'] = ErrorList(["Maximum number of choices is 6"])
            return self.form_invalid(form)
        
        chapter = Chapter.objects.get(pk = form.cleaned_data['chapter'])
        for inter in interests:
            try:
                interest = Interest.objects.get(interest = inter)
            except Interest.DoesNotExist:
                interest = Interest(interest = inter, status='custom' )
                interest.save()
            
            try: 
                deal = Deal.objects.get(chapter = chapter, interest = interest)
            except Deal.DoesNotExist:
                deal = Deal( chapter = chapter, interest = interest)
                deal.save()
                
        return HttpResponseRedirect( reverse('or_setup') )

def leadb( request ):
    template_name = 'organ/or_leadbuyer.html'
    
    if 'term' in request.GET:
        term  = Term.objects.get( pk = request.GET['term'])
        buyer = term.buyer
        connections = term.connections()
        
        profile = buyer.get_profile()
        context = { 'buyer':buyer, 'profile':profile, 'term':term, 'connections':connections}
        return render_to_response(template_name,context, context_instance=RequestContext(request) )
            
    
@login_required
def setup( request ):
    if request.method == 'GET':
        if 'no_header' in request.GET:
            context = { 'header':False }
        else: 
            context = { 'header':True }
            
    return render_to_response('organ/or_setup.html',context, context_instance=RequestContext(request) )


@login_required
def dashboard( request ):
    
    user = request.user
    if 'state' in request.GET:
        state = request.GET['state']
    else:
        state = None

    chapters = Chapter.objects.filter( organizer = user )
    if len( chapters ) > 1:
        pass
    
    chapter = chapters[0]
    
    active   = []
    pending  = []
    canceled = []
    
    for deal in chapter.deals():
        for term in deal.terms():
            if term.status == 'approved':
                active.append(term)
            
            elif term.status == 'pending':
                pending.append(term)
            
            elif term.status == 'canceled':
                canceled.append(term)
    today = date.today()      
    return render_to_response( 'organ/or_dash.html', 
                               {'chapter':chapter,'state':state, 'today':today, 'active':active, 'pending':pending, 'canceled':canceled }, 
                               context_instance=RequestContext(request) 
                             )


@login_required
def status( request ):
    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        if term.owner() == request.user and 'status' in request.GET:
            status = request.GET['status']
            if status in TERM_STATUS:
                term.status = request.GET['status']
                term.save()
            
                mail = Mail([term.buyer.email],
                            [term.deal.chapter.organizer.email],
                            'BrightMap Deal',
                            'deal_status.tmpl',
                            term = term,
                            url  = reverse('lb_dash')
                           )
                mail.send()
                
    return HttpResponseRedirect(reverse('or_dash'))


def events( request ):
    chapter = Chapter.objects.get(organizer = request.user )
    events  = Event.objects.filter( chapter = chapter).order_by('date').reverse()
    
    event_list = []

    for i, event in enumerate(events):
        if i > 12:
            break
        title      = event.describe[:75]
        date       = event.date.strftime('%d %b %Y')
        attendees  = event.attendees()
        surveys    = event.surveys(lead = True)
        connections= event.connections()
        commission = 0
        for c in connections:
            commission += c.term.cost
        
        commission = "%.2f" % ( float(commission) *.45 )   
        event_list.append( dict ( title       = title,
                                  date        = date, 
                                  attendees   = len(attendees), 
                                  surveys     = len(surveys),
                                  connections = len(connections),
                                  commission  = commission
                                )
                          )
        
    return render_to_response( 'organ/or_events.html', 
                               {'chapter':chapter,'events':event_list }, 
                               context_instance=RequestContext(request) 
                             )

   
def cancel(request):
    # Cancel Terms of a Deal
    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        term.status = 'canceled'
        term.save()
    return HttpResponseRedirect(reverse('or_dash'))

