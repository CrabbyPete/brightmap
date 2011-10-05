import settings
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

#Authorize imports
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST

#Local imports
from base.models                    import *
from social.models                  import *
from forms                          import *

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
    try:
        msg.send( fail_silently = False )
    except:
        err = "Email Send Error For: " + organizer.email
        logger.error(err)


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

@csrf_protect
def lb_apply(request):
    """
    Apply to buy a deal
    """
    def submit_form(form):
        c = {'form':form }
        return render_to_response( 'leadb/lb_apply.html', c,
                                   context_instance=RequestContext(request) )
    # GET
    if request.method == 'GET':
        form = ApplyForm()
        return submit_form(ApplyForm())

    # POST
    if request.method == 'POST':
        form = ApplyForm(request.POST)
        if not form.is_valid():
            return submit_form(form)

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
                             buyer  = request.user,
                             status = 'pending'
                            )
            expire.save()
            mail_organizer( request.user, deal, expire, deal_type )
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
                             buyer = request.user,
                             status = 'pending'
                            )
            cancel.save()
            mail_organizer( request.user, deal, cancel, deal_type )


    return HttpResponseRedirect(reverse('lb_dash'))

@csrf_protect
def lb_dash(request):
    """
    Show the buyers dash board
    """
    def submit_form(form, terms, connections ):
        c = { 'form':form, 'terms':terms,'connections':connections }
        return render_to_response( 'leadb/lb_dash.html', c,
                                   context_instance=RequestContext(request) )

    if request.method == 'GET':
        terms = Term.objects.filter(buyer = request.user)
        connections = Connection.objects.for_user(request.user)
        try:
            lb = LeadBuyer.objects.get(user = request.user)
        except LeadBuyer.DoesNotExist:
            lb = LeadBuyer(user = request.user)
            lb.save()

        form = BudgetForm(initial = {'budget':lb.budget})
        return submit_form(form, terms, connections)

    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if not form.is_valid():
            return submit_form(form)

        budget = form.cleaned_data['budget']
        lb = LeadBuyer.objects.get(user = request.user)
        lb.budget = budget
        lb.save()

        return HttpResponseRedirect(reverse('lb_dash'))

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

 

@csrf_protect
def lb_payment(request):

    def submit_form(form):
        c = {'form':form }
        return render_to_response( 'leadb/lb_payment.html', c,
                                   context_instance=RequestContext(request) )

    #GET
    if request.method == 'GET':
        form = CIMPaymentForm()
        return submit_form(form)

    #POST
    form = CIMPaymentForm(request.POST)
    if not form.is_valid():
        return submit_form(form)

    try:
        authorize = Authorize.objects.get(user = request.user)

    except Authorize.DoesNotExist:
        authorize = Authorize( user = request.user )
        authorize.customer_profile_id = unicode(1000 + request.user.pk)
        authorize.save()
        

    # Initialize the API class
    cim_api = cim.Api( unicode(settings.AUTHORIZE['API_LOG_IN_ID']),
                       unicode(settings.AUTHORIZE['TRANSACTION_ID']) 
                      )
    
    # Get the card and expiration date
    card_number     = form.cleaned_data[u'card_number']
    expiration      = form.cleaned_data[u'expiration_date']
    expiration      = unicode( expiration.strftime(u'%Y-%m') )


    # Create a Authorize.net CIM profile
    try:
        response = cim_api.create_profile( card_number = card_number,
                                           expiration_date = expiration,
                                           email = request.user.email,
                                           customer_id = authorize.customer_id
                                          )
    except Exception, e:
        result = 'NG'
    else:
        # Check to see it if its OK
        result = response.messages.result_code.text_.upper()
    
    # Check the reply
    if result == 'OK':
        authorize.profile_id = response.customer_profile_id.text_
        authorize.save()
        
        profile = request.user.get_profile()
        profile.is_ready = True
        profile.save()
        
        #profile = cim_api.get_profile( customer_profile_id = authorize.profile_id )
    else:
        # Log an error
        pass
 
    return HttpResponseRedirect(reverse('lb_dash'))

