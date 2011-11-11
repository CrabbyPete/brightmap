import settings
import logging
logger = logging.getLogger('leadbuer')


from datetime                       import datetime
from dateutils                      import relativedelta

# Django imports
from django.views.generic.base      import  TemplateView
from django.views.generic.edit      import  FormView
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.http                    import  HttpResponseRedirect
from django.forms.util              import  ErrorList
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext, Context, loader
from django.views.decorators.csrf   import  csrf_protect
from django.core.urlresolvers       import  reverse
from django.core.mail               import  EmailMultiAlternatives

#Authorize imports
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_LIVE, CREDIT_CARD
from authorize.responses            import AuthorizeError #, _cim_response_codes

#Local imports
from base.models                    import ( LeadBuyer, Chapter, Expire, Cancel, Connection, Authorize,
                                             Deal, Term, Interest, Profile
                                            )

from social.models                  import LinkedInProfile


from forms                          import DEAL_CHOICES, BuyerForm, ApplyForm, PaymentForm
from geo                            import geocode

def mail_organizer( user, deal, term, deal_type ):
    # Render the letter
    organizer = deal.chapter.organizer
    
    c = Context({'user' : user,
                 'deal' : deal,
                 'term' : term,
                 'type' : deal_type
                })
    
    template = loader.get_template('letters/request.tmpl')
    message = template.render(c)

    subject = "New BrightMap LeadBuyer Request: %s"%(deal.interest)
    recipients = [ organizer.email ]

    msg = EmailMultiAlternatives( subject,
                                  message,
                                  'requests@brightmap.com',
                                  recipients,
                                  ['requests@brightmap.com']
                                )
    if settings.SEND_EMAIL:
        try:
            msg.send( fail_silently = False )
        except:
            err = "Email Send Error For: " + organizer.email
            logger.error(err)


class  SignUp( FormView ):
    template_name = 'leadb/signup.html'
    form_class    = BuyerForm

    def form_valid( self, form ):

        # Get the email address and see if they are in the database
        email          = form.cleaned_data['email']
        email_verify   = form.cleaned_data['email_verify']
        if email != email_verify:
            form._errors['email'] = ErrorList(["The emails do not match"])
            return self.form_invalid(form)
    
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
        else:
            if not user.check_password(password) and profile.is_ready:
                form._errors['password'] = ErrorList(["User exist with a different password"])
                return self.form_invalid(form)
            else:
                user.set_password(password)
                user.save()
            
        profile.is_leadbuyer = True
        profile.is_agreed    = True
      
        profile.phone = form.cleaned_data['phone']
        profile.address = form.cleaned_data['address']
        profile.company = form.cleaned_data['company']
        profile.title = form.cleaned_data['title']
        profile.website = form.cleaned_data['website']
        profile.twitter = form.cleaned_data['twitter']
        profile.linkedin = form.cleaned_data['linkedin']
    
        profile.save()
    
        # Check if there is a leadbuyer record for this user
        try:
            leadb = LeadBuyer.objects.get(user = user)
        except LeadBuyer.DoesNotExist:
            leadb = LeadBuyer(user = user)
            leadb.save()

        # Login the new user
        user = auth.authenticate(username=user.username, password=password)
        if user is not None and user.is_active:
            auth.login(self.request, user)

        return HttpResponseRedirect ( reverse('lb_payment') )

 
@csrf_protect
def lb_profile(request):
    """
    Edit LeadBuyer profile details
    """
    def submit_form(form):
        c = {'form':form }
        return render_to_response( 'leadb/lb_profile.html', c,
                                   context_instance=RequestContext(request) )

    default_password = '123456789012345'

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
                    'first_name':   user.first_name,
                    'last_name':    user.last_name,
                    'email':        user.email,
                    'password':     default_password,
                    'pass_confirm': default_password,
                    'phone':        buyer.phone,
                    'title':        buyer.title,
                    'company':      buyer.company,
                    'address':      buyer.address,
                    'website':      buyer.website,
                    'agree':        buyer.is_agreed
                    }
        else:
            data = {
                    'first_name':   user.first_name,
                    'last_name':    user.last_name,
                    'email':        user.email,
                    'password':     default_password,
                    'pass_confirm': default_password,
                    'phone':        buyer.phone,
                    'title':        linkedin.title,
                    'company':      linkedin.company,
                    'address':      buyer.address,
                    'website':      buyer.website,
                    'agree':        buyer.is_agreed
                    }

        form = BuyerForm(data)
        return submit_form(form)

    # POST
    user    = request.user
    profile = user.get_profile()
 
    form = BuyerForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    # Make sure they agreed to terms at least once
    if not profile.is_agreed and not form.cleaned_data['agree']:
        form._errors['agree'] = ErrorList(["Please check agreement"])
        return submit_form(form)
    profile.is_agreed = True
    
    # Get the email and see if they want to change it
    email = form.cleaned_data['email']
    if email != user.email:
        qry = User.objects.filter(email = email)
        if qry.count() >= 1:
            form.errors['email'] = "This email is in use"
            return submit_form(form)
        else:
            user.email = email

    user.first_name = form.cleaned_data['first_name']
    user.last_name = form.cleaned_data['last_name']

    # Check password input
    password = form.cleaned_data['password']
    pass_confirm = form.cleaned_data['pass_confirm']
    if password != default_password:
        if password != pass_confirm:
            form._errors['password'] = ErrorList(["The passwords do not match"])
            return submit_form(form)
        else:
            user.set_password(password)

    user.save()
   
    # Edit profile
    profile.is_leadbuyer = True
    
    # If they don't agree this is a waste
    if not profile.is_agreed and not form.cleaned_data['agree']:
        form._errors['agree'] = ErrorList(["Please check agreement"])
        return submit_form(form)
    profile.is_agreed = True
    
    profile.phone   = form.cleaned_data['phone']
    profile.address = form.cleaned_data['address']
    profile.company = form.cleaned_data['company']
    profile.website = form.cleaned_data['website']
    profile.title   = form.cleaned_data['title']

    profile.save()

    try:
        leadbuyer = LeadBuyer.objects.get( user = user)
    except LeadBuyer.DoesNotExist:
        leadbuyer = LeadBuyer(user = user)
        leadbuyer.save()

    return HttpResponseRedirect(reverse('lb_dash'))

# Initialize the TYPE List form form.DEAL_CHOICES
DEAL_TYPES = [c[0] for c in DEAL_CHOICES]


class Apply( FormView ):
    """
    Apply to buy a deal
    """
    template_name = 'leadb/lb_apply.html'
    form_class    = ApplyForm
    
    def form_valid(self,form):
        """
        Process a valid application form
        """
        chapter   = form.cleaned_data['chapter']
        interest  = form.cleaned_data['interest']
        deal_type = form.cleaned_data['deal_type']
        
        # Make sure a deal type was chosen
        if not deal_type in DEAL_TYPES:
            form._errors['deal_type'] = ErrorList(["Please choose one"])
            return submit_form(form)

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
            expire = Expire( deal   = deal,
                             date   = one_month,
                             cost   = 0,
                             buyer  = self.request.user,
                             status = 'pending'
                            )
            expire.save()
            mail_organizer( self.request.user, deal, expire, deal_type )
        else:
            if deal_type == 'Exclusive':
                cost = 50
                exclusive = True

            elif deal_type ==  'Nonexclusive':
                cost = 20
                exclusive = False

            elif deal_type == 'Sponsored':
                cost = 0
                exclusive = True

            cancel = Cancel( deal = deal,
                             cost = cost,
                             exclusive = exclusive,
                             buyer = self.request.user,
                             status = 'pending'
                            )
            cancel.save()
            mail_organizer( self.request.user, deal, cancel, deal_type )

        return HttpResponseRedirect(reverse('lb_dash'))


class Dash( TemplateView ):
    """
    Show the buyers dash board
    """
    template_name = 'leadb/lb_dash.html'
    
    """
    <td class="recivedcontent">Web Design / Development</td>
    <td class="recivedcontent">Tech Drinkup</td>
    <td class="recivedcontent">Exclusive</td>
    <td class="recivedcontent">12-Jun-11</td>
    <td class="recivedcontent">20</td>
    <td class="recivedcontent">$50</td>
    <td class="recivedcontent">$1000</td>
    <td class="recivedcontent interestright"><a href="#">Cancel</a></td>
    """
    def get_context_data(self, **kwargs):
        buyer = self.request.user
        terms = Term.objects.filter(buyer = buyer)
        args = dict(terms = terms)
        return args

 
def lb_details(request):
    
    def submit_form(connections):
        c = {'connections':connections }
        return render_to_response( 'leadb/lb_details.html', c,
                                   context_instance=RequestContext(request) )

    #GET
    if request.method == 'GET':
        if 'term' in request.GET:
            term = Term.objects.get(pk=request.GET['term'])
            connections = Connection.objects.filter(term = term)
        else:
            connections = Connection.objects.for_user(request.user)
        return submit_form(connections)

 
class Payment( FormView ):
    template_name = 'leadb/lb_payment.html'
    form_class    = PaymentForm

    def form_valid(self, form):

        user    = self.request.user
        profile = user.get_profile()
    
        # Get the current Authorize record or create a new one
        try:
            authorize = Authorize.objects.get( user = user )

        except Authorize.DoesNotExist:
            authorize = Authorize( user = user )
            customer_id = 1000 + user.pk
            authorize.customer_id = str( customer_id )
            authorize.save()

        # Get the LeadBuy record
        try:
            lb = LeadBuyer.objects.get( user = user )
        except LeadBuyer.DoesNotExist:
            form._errors['budget'] = ErrorList(["Apply as leader first"])
            return self.form_invalid(form)
 
        # Initialize the API class
        cim_api = cim.Api( unicode(settings.AUTHORIZE['API_LOG_IN_ID']),
                           unicode(settings.AUTHORIZE['TRANSACTION_ID']) 
                         )
    
        # Get the card, expiration date, address and budget
        card_number = form.cleaned_data[u'number']
        expiration  = form.cleaned_data[u'expiration'].strftime(u'%Y-%m')
        budget      = form.cleaned_data['budget']
        address     = form.cleaned_data['address']
        city        = form.cleaned_data['city']
        state       = form.cleaned_data['state']
    
        billing = dict( bill_first_name = user.first_name,
                        bill_last_name  = user.last_name,
                        bill_company    = profile.company,
                        bill_phone      = profile.phone
                      )
    
        # Use Google to verify the address string
        address += ", " + city + " " + state
        if address:
            try:
                local = geocode(address)
            except Exception, e:
                form._errors['address'] = ErrorList(["Not a valid address"])
                return self.form_invalid(form)

            billing['bill_address'] = local.get('street',None)
            billing['bill_city']    = local.get('city',None)
            billing['bill_state']   = local.get('state',None)
            billing['bill_zip']     = local.get('zipcode',None)
            billing['bill_country'] = local.get('country',None)
        
        # Save the address
        profile.address = local['address']
 
        # Create a Authorize.net CIM profile
        kw = dict ( card_number     = card_number,
                    expiration_date = unicode(expiration),
                    customer_id     = unicode( authorize.customer_id ),          
                    profile_type    = CREDIT_CARD,
                    email           = user.email,
                    validation_mode = VALIDATION_LIVE
                  )
    
        kw.update(billing)
        try:
            response = cim_api.create_profile( **kw )
 
        except AuthorizeError, e:
            form._errors['card_number'] = ErrorList([e])
            return self.form_invalid(form)
 
        # Check to see it if its OK
        result = response.messages.result_code.text_
        if result != 'Ok':
            form._errors['card_number'] = ErrorList( [response.messages.message.text_] )
            return self.form_invalid(form)
    
        authorize.profile_id      = response.customer_profile_id.text_
        authorize.payment_profile = response.customer_payment_profile_id_list.numeric_string.text_
        authorize.save()
    
        # Check if there was a budget input
        if budget:
            lb.budget = budget
            lb.save()
    
        profile.is_ready = True
        profile.save()
 
        return HttpResponseRedirect(reverse('lb_apply'))

