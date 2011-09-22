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

#Local imports
from base.models                    import *
from social.models                  import *
from forms                          import *

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
    user = request.user
    form = BuyerForm(request.POST)
    if not form.is_valid():
        return submit_form(form)


    # If they don't agree this is a waste
    if not form.cleaned_data['agree']:
        form._errors['agree'] = ErrorList(["Please check agreement"])
        return submit_form(form)

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
    profile = user.get_profile()
    profile.is_agreed = True
    profile.is_leadbuyer = True

    profile.phone   = form.cleaned_data['phone']
    profile.address = form.cleaned_data['address']
    profile.company = form.cleaned_data['company']
    profile.website = form.cleaned_data['website']
    profile.is_ready = True
    profile.save()

    return HttpResponseRedirect(reverse('lb_dash'))

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
        else:
            if deal_type == 'Exclusive':
                cost = 50
                exclusive = True
            elif deal_type ==  'Nonexclusive':
                cost = 20
                exclusive = False

            cancel = Cancel( deal = deal,
                             cost = cost,
                             exclusive = exclusive,
                             buyer = request.user,
                             status = 'pending'
                            )
            cancel.save()
    try:
        payment = Payment.objects.get(user = user)
    except:
        return HttpResponseRedirect(reverse('lb_payment'))

    return HttpResponseRedirect(reverse('lb_profile'))


def lb_dash(request):
    """
    Show the buyers dash board
    """
    def submit_form(connections):
        c = {'connections':connections }
        return render_to_response( 'leadb/lb_dash.html', c,
                                   context_instance=RequestContext(request) )

    if request.method == 'GET':
        connections = Connection.objects.for_user(request.user)
        return submit_form(connections)

    if request.method == 'POST':
            return HttpResponseRedirect('/')

from authorize import cim
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

    cim_api = cim.Api( unicode(settings.AUTHORIZE['API_LOG_IN_ID']),
                       unicode(settings.AUTHORIZE['TRANSACTION_ID']) ,
                       is_test=True
                      )

    card_number     = form.cleaned_data['card_number']
    expiration      = form.cleaned_data['expiration_date']
    expiration      = unicode( expiration.strftime(u"%Y-%m") )

    csc             = form.cleaned_data['card_code']

    tree = cim_api.create_profile( card_number = card_number,
                                   expiration_date = expiration,
                                   customer_id = request.user.email
                                 )
    profile_id = tree.customer_profile_id.text_
    tree = cim_api.get_profile( customer_profile_id = profile_id )
    ret = cim_api.delete_profile( customer_profile_id = profile_id )

    return HttpResponseRedirect('/')

"""
 We create a profile for one of our users.
tree = cim_api.create_profile(
    card_number=u"4111111111111111",
    expiration_date=u"2008-07",
    customer_id=u"test_account")

# Store the profile id somewhere so that we can later retrieve it.
# CIM doesn't have a listing or search functionality so you'll
# have to keep this somewhere safe and associated with the user.
profile_id = tree.customer_profile_id.text_

# Retrieve again the profile we just created using the profile_id
tree = cim_api.get_profile(customer_profile_id=profile_id)
pprint(tree)

# And let's now try to create a transaction on that profile.
resp = cim_api.create_profile_transaction(
    customer_profile_id=profile_id,
    amount=50.0
)
pprint(resp)

# We did what we needed, we can remove the profile for this example.
pprint(cim_api.delete_profile(customer_profile_id=profile_id))
"""
