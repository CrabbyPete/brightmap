# Python imports
import  logging
logger = logging.getLogger('organizer')

from datetime                       import datetime

# Django imports
from django.views.generic.edit      import  FormView
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.forms.util              import  ErrorList
from django.core.urlresolvers       import  reverse
from django.http                    import  HttpResponseRedirect
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext

#Local imports
from base.models                    import Profile, Organization, Chapter, Interest, Deal, Event
from forms                          import OrganizerForm, CategoryForm



class SignUp( FormView ):
    template_name = 'organ/signup.html'
    form_class    = OrganizerForm
    password      ='2434&)%*%%^$#@' 
    
    def get_initial( self ):
        if self.request.method == 'GET':
            if self.request.user.is_authenticated():
                self.initial = dict ( email         = self.request.user.email,
                                      email_verify  = self.request.user.email,
                                      first_name    = self.request.user.first_name,
                                      last_name     = self.request.user.last_name,
                                      password      = self.password,
                                      pass_confirm  = self.password 
                                    )
        else:
            self.initial = {}
        
        return self.initial

    def form_valid( self, form ):
        """
        Process the validated Event Organizer signup page
        """
    
        # Get the email address and see if they are in the database
        email          = form.cleaned_data['email']
        """
        email_verify   = form.cleaned_data['email_verify']
        if email != email_verify:
            form._errors['email'] = ErrorList(["The emails do not match"])
            return self.form_invalid(form)
        """
        
        # Check the passwords match
        password     = form.cleaned_data['password']
        pass_confirm = form.cleaned_data['pass_confirm']
        if password != pass_confirm:
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
            if not user.check_password(password) and profile.is_ready:
                form._errors['password'] = ErrorList(["User exist with a different password"])
                return self.form_invalid(form)
            else:
                user.set_password(password)
                user.save()
            
        profile.is_agreed    = True
        profile.is_organizer = True
        
        # See if the organization and chapter exist
        name = form.cleaned_data['organization']
        try:
            organization = Organization.objects.get( name = name )
        except Organization.DoesNotExist:
            organization = Organization( name = name )
            organization.save()
    
        
        # See if the chapter exists. If its blank its the same as the organization name
        if form.cleaned_data['chapter'] != '':
            name = form.cleaned_data['chapter']
        try:
            chapter = Chapter.objects.get( name = name, organization = organization )
        
        except Chapter.DoesNotExist:
            chapter = Chapter( name = name, organizer = user, organization = organization )
            chapter.save()
            
        profile.save()
    
        # Login the new user
        user = auth.authenticate(username=user.username, password=password)
        if user is not None and user.is_active:
            auth.login(self.request, user)

        return HttpResponseRedirect( reverse('or_category')+'?chapter='+str(chapter.id) )

class Category( FormView ):
    template_name = 'organ/category.html'
    form_class    = CategoryForm
    
    """
    def get_initial( self ):
        if self.request.method == 'GET':
            chapter = self.request.GET['chapter']
            return  {'chapter':chapter }
    """

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
            form._errors['standard'] = ErrorList(["Max number of choices is 6"])
            return self.form_invalid(form)
        
        chapter = Chapter.objects.get(pk = form.cleaned_data['chapter'])
        for inter in interests:
            try:
                interest = Interest.objects.get(interest = inter)
            except Interest.DoesNotExist:
                interest = Interest(interest = inter, level = 3 )
                interest.save()
            
            try: 
                deal = Deal.objects.get(chapter = chapter, interest = interest)
            except Deal.DoesNotExist:
                deal = Deal( chapter = chapter, interest = interest)
                deal.save()
                
        
        return HttpResponseRedirect( reverse('or_setup') )

def setup( request ):
    return render_to_response('organ/setup.html', {}, context_instance=RequestContext(request) )

def union(a, b):
    """ return the union of two lists """
    return list(set(a) | set(b))

def dashboard( request ):
    user = request.user

    chapters = Chapter.objects.filter( organizer = user )
    
    # Get the range of days for this month
    month = datetime.today()
    first = month.replace( day = 1 )
    last  = first.replace( month = first.month + 1 ) - datetime.timedelta (days = 1)
    
    dates = (first, last)

    interests = []
    report = {}
    
    for chapter in chapters:
        interests =  union( interests, chapter.interests() )
        
    for interest in interests:
        for chapter in chapters:
            for event in Event.objects.filter( chapter = chapter, date__range = dates ):
                connections =  event.connections( interest = interest )
    
    return render_to_response('organ/dashboard.html', {}, context_instance=RequestContext(request) )

    