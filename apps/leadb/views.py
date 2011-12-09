import re
import settings
import logging
logger = logging.getLogger('leadbuyer')


from datetime                       import datetime
from dateutils                      import relativedelta

# Django imports
from django.views.generic.base      import  TemplateView
from django.views.generic.edit      import  FormView
from django.template                import  loader, Context
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.contrib.auth.decorators import  login_required
from django.http                    import  HttpResponseRedirect
from django.forms.util              import  ErrorList
from django.core.urlresolvers       import  reverse
from django.core.mail               import  EmailMultiAlternatives

#Authorize imports
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_LIVE, VALIDATION_TEST, CREDIT_CARD
from authorize.responses            import AuthorizeError #, _cim_response_codes

#Local imports
from base.models                    import ( LeadBuyer, Chapter, Expire, Cancel, Connection, Authorize,
                                             Deal, Term, Interest, Profile, Invoice
                                            )
from base.forms                     import LoginForm

from social.models                  import LinkedInProfile

from forms                          import DEAL_CHOICES, BuyerForm, ApplyForm, PaymentForm

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
    recipients = [ organizer.email, term.buyer.email ]

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
    initial          = {}
    template_name    = 'leadb/signup.html'
    form_class       = BuyerForm
    default_password = 'A&^%4562#$743D~5RT'
    
    
    def get_initial(self):
        """
        Get initial values for the Signup/Profile page
        """    
        if self.request.method == 'GET': 
              
            # Someone changing profile data
            if self.request.user.is_authenticated():
                user = self.request.user
                profile = user.get_profile()
        
                # A new user is signing up
            else:
                return {}

            # Check if they have a LinkedIn profile
            """
            try:
                linkedin = LinkedInProfile.objects.get(user = user)
            except LinkedInProfile.DoesNotExist:
                pass
            """
            self.initial = {
                    'first_name':   user.first_name,
                    'last_name':    user.last_name,
                    'email':        user.email,
                    'email_verify': user.email,
                    'password':     self.default_password,
                    'pass_confirm': self.default_password,
                    'phone':        profile.phone,
                    'title':        profile.title,
                    'company':      profile.company,
                    'address':      profile.address,
                    'website':      profile.website,
                    'agree':        profile.is_agreed
                }

            return self.initial
  
    
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
            
            # Log them in
            user = auth.authenticate(username=user.username, password=password)
            if user is not None and user.is_active:
                auth.login(self.request, user)

        else:
            if password != self.default_password:
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
        custom    = form.cleaned_data['custom']
        
        # Make sure a deal type was chosen
        if not deal_type in DEAL_TYPES:
            form._errors['deal_type'] = ErrorList(["Please choose one"])
            return self.form_invalid(form)

        # Check if this is a custom request
        if custom:
            interest = Interest( interest = custom, status = 'custom')
            interest.save()
        else:
            interest = Interest.objects.get(interest = interest)
        
        # Check if there are any existing deals
        chapter  = Chapter.objects.get(name = chapter)
        try:
            deal = Deal.objects.get( chapter = chapter, interest = interest )

        # If not create one
        except Deal.DoesNotExist:
            deal = Deal( chapter = chapter, interest = interest )
            deal.save()

        # Check the type of deal
        if custom:
            deal_type = 'Exclusive'
            cancel = Cancel( deal = deal,
                             cost = 50,
                             exclusive = True,
                             buyer = self.request.user,
                             status = 'pending'
                            )
            cancel.save()
            mail_organizer( self.request.user, deal, cancel, deal_type )
        
        
        elif deal_type == 'Trial':
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

        return HttpResponseRedirect(reverse('lb_apply'))

class Dash( TemplateView ):
    """
    Show the buyers dash board
    """
    template_name = 'leadb/lb_dash.html'
    
    def get_context_data(self, **kwargs):
        buyer = self.request.user
        terms = Term.objects.filter(buyer = buyer)

        term_list = []
        total     = 0.0
        for term in terms:
            args = dict ( interest    = term.deal.interest.interest,
                          chapter     = term.deal.chapter.name,
                          date        = term.modified,
                          connections = len(term.connections()),
                          cost        = term.cost,
                          total       = term.total(),
                          pk          = term.pk
                         )
            
            total += float(args['total'])
            if term.status == 'canceled':
                status = 'Canceled'
            
            elif term.status == 'pending':
                status = 'Pending'
            
            elif term.cancel:
                if term.exclusive:
                    status = 'Exclusive'
                else:
                    status = 'Non-Exclusive'
            
            else:
                status = 'Trail'
        
            args.update(status = status)
            term_list.append(args)

        # Convert total to a string
        total = '%10.2f'%total
        total = dict(total = total)
        kwargs = dict( terms = term_list, total = total ) # {terms:terms, total:total, invoices:invoices }
        
        # Now get Invoices and put them in an 4 wide  array
        invoices = []
        l4 = []
        for i, invoice in enumerate(Invoice.objects.filter(user = buyer)):
            if i % 4 == 0:
                if i:
                    invoices.append(l4)
                
                l4 = [invoice]
            else:
                l4.append(invoice) 
        invoices.append(l4)
        
        kwargs.update(invoices=invoices)
        return kwargs
    
    
class Bill( TemplateView ):
    template_name = 'leadb/lb_bills.html'
    
    def get_context_data(self):
        if 'invoice' in self.request.GET:
            invoice = Invoice.objects.get(pk=self.request.GET['invoice'])
            connections = invoice.connections()
            title = invoice.title
            
            total = 0.0
            bills = []
            for connection in connections:
                detail = dict( organization = connection.survey.event.chapter.name,
                               event        = connection.survey.event.describe,
                               date         = connection.survey.event.date,
                               name         = connection.survey.attendee.first_name + ' ' + connection.survey.attendee.last_name, 
                               email        = connection.survey.attendee.email,
                               company      = connection.survey.attendee.get_profile().company,
                               connected    = connection.date,
                               price        = connection.term.cost
                              )
                bills.append(detail)
                total += float(detail['price'])
            
            bills = dict(bills = bills, total = total, title = title )
        return bills
    


regex_money = '^\$?([1-9]{1}[0-9]{0,2}(\,[0-9]{3})*(\.[0-9]{0,2})?|[1-9]{1}[0-9]{0,}(\.[0-9]{0,2})?|0(\.[0-9]{0,2})?|(\.[0-9]{1,2})?)$'
regex_suba  = "(APT|APARTMENT|BLDG|BUILDING|DEPT|DEPARTMENT|FL|FLOOR|HNGR|HANGER|LOT|PIER|RM|ROOM|TRLR|TRAILER|UNIT|SUITE|STE|BOX)"
regex_pob   = "((P\.O\. BOX)|(P\.O BOX)|(PO BOX)|(POBOX)|(P O BOX))"

def parse_address(address):
    """
    Authorize.net address verification does not care about sub address and po boxs should be
    # PO Box format eg 123 PO Box
    """
    po   = re.compile(regex_pob,  re.I)
    found = po.search(address)
    if found:
        where = address.find(found.group(0))
        a2 = address[where:]
        n = re.sub("\D", "", a2)
        a2 = a2.replace(n,"")
        a2 = n+' '+a2
        return a2
    else:
        subs = re.compile(regex_suba, re.I)
        found = subs.search(address)
        if found:
            where = address.find(found.group(0))
            return address[0:where]

class Payment( FormView ):
    template_name = 'leadb/lb_payment.html'
    form_class    = PaymentForm
    
    def get_initial(self):
        """
        Fill in as much of the Payment form as possible
        """
        # Only do this on a GET
        if not self.request.method == 'GET':
            return {}
        
        # Find what budget they currently have
        try:
            lb = LeadBuyer.objects.get(user = self.request.user)
        except LeadBuyer.DoesNotExist:
            budget = '$500.00'
        else:
            if lb.budget:
                budget = lb.budget
            else: 
                budget ='$500.00'
        
        # Parse the address
        profile = self.request.user.get_profile()
        if profile.address:
            billing = profile.address.split('$')
            return dict ( address = billing[0],
                          city    = billing[1],
                          state   = billing[2],
                          zipcode = billing[3],
                          budget  = budget
                        )
        else:
            return dict ( budget = budget )

    def form_valid(self, form):
        """
        Process a valid credit card and budget form
        """
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
 
        # Check the expiration date
        expiration  = form.cleaned_data['expire_year']+'-'+form.cleaned_data['expire_month']
        
        expire = datetime.strptime(expiration,'%Y-%m').replace( day = 1 )
        if expire < datetime.today():
            form._errors['expire_year'] = ErrorList(["Date is in the past"])
            return self.form_invalid(form)
        

        # Get the card, expiration date, address and budget
        card_number = form.cleaned_data[u'number']
        address     = form.cleaned_data['address']
        city        = form.cleaned_data['city']
        state       = form.cleaned_data['state']
        zipcode     = form.cleaned_data['zipcode']
        budget      = form.cleaned_data['budget']
        
        # Check if they checked a budget put in a valid $ value. Budget is a tuple ('Budget',value)
        money = re.compile('^\$?([1-9]{1}[0-9]{0,2}(\,[0-9]{3})*(\.[0-9]{0,2})?|[1-9]{1}[0-9]{0,}(\.[0-9]{0,2})?|0(\.[0-9]{0,2})?|(\.[0-9]{1,2})?)$')
        money = money.match(budget)
        if not money or budget == '':
            form._errors['budget'] = ErrorList(["Not a valid dollar amount"])
            return self.form_invalid(form)
        lb.budget = money.groups()[0]
               
            
        # Prepare the required parameters 
        billing = dict( bill_first_name = user.first_name,
                        bill_last_name  = user.last_name,
                        bill_company    = profile.company,
                        bill_phone      = profile.phone
                      )
    
        # Look for any sub addresses like Apt, Building .. and dump them
        sub_address = parse_address( address )
        if sub_address and sub_address != address:
            address = sub_address
  
        billing.update( bill_address = address )
        billing.update( bill_city    = city    )
        billing.update( bill_state   = state   )
        billing.update( bill_zip     = zipcode )
 
        
        # Save the address
        profile.address = address+'$'+city+'$'+state+'$'+zipcode
 
        # Create a Authorize.net CIM profile
        kw = dict ( card_number     = card_number,
                    expiration_date = unicode(expiration),
                    customer_id     = unicode( authorize.customer_id ),          
                    profile_type    = CREDIT_CARD,
                    email           = user.email,
                    validation_mode = VALIDATION_LIVE
                  )
    
        kw.update(billing)
        
        # Initialize the API class
        cim_api = cim.Api( unicode(settings.AUTHORIZE['API_LOG_IN_ID']),
                           unicode(settings.AUTHORIZE['TRANSACTION_ID']) 
                         )
    
        try:
            response = cim_api.create_profile( **kw )
 
        except Exception:
            form._errors['card_number'] = ErrorList( ['Credit Card Authorization Failed'] )
            return self.form_invalid(form)
        
        # Check to see it if its OK
        result = response.messages.result_code.text_
        
        if result != 'Ok':
            form._errors['number'] = ErrorList( [response.messages.message.text.text_] )
            return self.form_invalid(form)
    
        authorize.profile_id      = response.customer_profile_id.text_
        authorize.payment_profile = response.customer_payment_profile_id_list.numeric_string.text_
        authorize.save()
    
        # Save any leadbuy changes
        lb.save()
         
        # Save profile changes and indicate the credit card is ready
        profile.is_ready = True
        profile.save()
 
        return HttpResponseRedirect(reverse('lb_apply'))

@login_required
def cancel_term(request):
    # Cancel Terms of a Deal
    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        term.status = 'canceled'
        term.save()
    return HttpResponseRedirect(reverse('lb_dash'))

@login_required
def renew_term(request):
    # Renew a deal that was canceled
    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        term.status = 'pending'
        term.save()
        # Send email to organizer
    return HttpResponseRedirect(reverse('lb_dash'))