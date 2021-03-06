import re
import settings


from datetime                       import datetime
from dateutils                      import relativedelta

# Django imports
from django.views.generic.base      import  TemplateView, View
from django.views.generic.edit      import  FormView
from django.template                import  RequestContext, loader, Context
from django.contrib                 import  auth
from django.contrib.auth.models     import  User
from django.http                    import  HttpResponseRedirect, HttpResponse
from django.shortcuts               import  render_to_response
from django.forms.util              import  ErrorList
from django.core.urlresolvers       import  reverse
from django.contrib.auth.decorators import  login_required

#Authorize imports
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_LIVE, VALIDATION_TEST, CREDIT_CARD
from authorize.responses            import AuthorizeError #, _cim_response_codes

#Local imports
from base.models                    import ( LeadBuyer, Chapter, Expire, Cancel, Connection, Authorize,
                                             Deal, Term, Interest, Profile, Invoice, TERM_STATUS, Expire,
                                             Invite
                                            )

from base.forms                     import LoginForm
from base.mail                      import Mail 

#from social.models                  import LinkedInProfile
from multipleforms                  import MultipleFormsView
from forms                          import ( DEAL_CHOICES, BuyerForm, ApplyForm,  
                                             PaymentForm, PaymentBudgetForm, BudgetForm
                                           )

def mail_organizer( user, deal, term, deal_type ):
    # Render the letter
    organizer  = deal.chapter.organizer
    sender     = 'deals@brightmap.com'
    if deal_type == 'cancel': 
        subject    = deal.chapter.name + ' deal canceled: ' + user.first_name + ' '+ user.last_name
        recipients = [ organizer.email ]
        template_name = 'canceled.tmpl'
    else:
        subject    = deal.chapter.name + ' sponsorship: ' + user.first_name + ' '+ user.last_name
        recipients = [ organizer.email, term.buyer.email ]
        template_name = 'request.tmpl'

    mail = Mail( sender, 
                 recipients, 
                 subject, 
                 template_name = template_name, 
                 user =  user,
                 deal = deal,
                 term = term,
                 type = deal_type
               )
    mail.send()
    return 

 
class  SignUpView( FormView ):
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
                if 'invite' in self.request.GET:
                    invite = Invite.objects.get(pk = self.request.GET['invite'] )
                    profile = invite.user.get_profile()
                    self.initial = {
                                    'invite':       str(invite.pk),
                                    'first_name':   invite.user.first_name,
                                    'last_name':    invite.user.last_name,
                                    'email':        invite.user.email,
                                    'phone':        profile.phone,
                                    'title':        profile.title,
                                    'company':      profile.company,
                                   }

                    return self.initial
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
                    'agree':        profile.is_agreed,
                    'twitter':      profile.twitter,
                    'linkedin':     profile.linkedin
                }

            return self.initial
  
    
    def form_valid( self, form ):

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
        """
        pass_confirm = form.cleaned_data['pass_confirm']
        if password != pass_confirm:
            form._errors['password'] = ErrorList(["The passwords do not match"])
            return self.form_invalid(form)
        """
        # Invite is a hiddenfield to carry the invitation
        invite = form.cleaned_data['invite']
        
        # Make sure they agree
        if not form.cleaned_data['agree']:
            form._errors['agree'] = ErrorList(["Please check agreement"])
            return self.form_invalid(form)
    
        # Get or create a user
        user = self.request.user
        
        # Is this someone new
        if user.is_anonymous():
            try:
                user = User.objects.get(email = email)
            except User.DoesNotExist:
                username = email[0:30]
                user  = User.objects.create_user( username = username,
                                                  email = email,
                                                  password = password
                                                )
                profile = Profile( user = user)
                profile.save()
            else:
                # Is an existing user signing up as a leadbuyer, check if they were an attendee
                profile = user.get_profile()
                if profile.is_agreed:
                    if not user.check_password(password) and not invite:
                        form._errors['email'] = ErrorList(["This email already exists"])
                        return self.form_invalid( form )
                    
        elif email != user.email:
            try:
                User.objects.get(email = email)
            except User.DoesNotExist:
                user.email = email
            else:
                invite = form.cleaned_data['invite']
                if not user.check_password(password):
                    form._errors['email'] = ErrorList(["This email already exists"])
                    return self.form_invalid( form )
        
        
        user.first_name = form.cleaned_data['first_name'].capitalize()
        user.last_name  = form.cleaned_data['last_name'].capitalize()
        if password != self.default_password:
            user.set_password(password)
        user.save()
            
        # Update profile details
        profile = user.get_profile()
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

        # If you already have payment details go to dashboard
        if profile.is_ready:
            return HttpResponseRedirect ( reverse('lb_dash')+"?state=profile" )
        else:
            if invite:
                return HttpResponseRedirect ( reverse('lb_apply')+'?invite='+invite )
            return HttpResponseRedirect ( reverse('lb_apply') )


# Initialize the TYPE List form form.DEAL_CHOICES
DEAL_TYPES = [c[0] for c in DEAL_CHOICES]

class ApplyView( FormView ):
    """ Apply to buy a deal """
    template_name = 'leadb/lb_community_two.html'
    form_class    = ApplyForm
    
    def get( self, request, *argv, **kwargs ):
        """
        Handle GET for apply form, Limit trials to one
        """
        expire = Expire.objects.filter( buyer = request.user, status = 'approved')
        data = dict()
        if len ( expire ) > 0:
            expire = True
        else:
            expire = False
        
        if 'invite' in request.GET:
            invite = Invite.objects.get(pk = request.GET['invite'])
            chapter = invite.chapter
            data.update( chapter = chapter, custom = invite.category )
            self.form_class = ApplyForm(initial=data)
        else: 
            if 'chapter' in request.GET:
                data.update( chapter = Chapter.objects.get(pk = request.GET['chapter']) )
 
            chapter = Chapter.objects.all().order_by('name')[0]
            self.form_class = ApplyForm(initial=data)
        
        try:
            lb = LeadBuyer.objects.get( user = request.user )
        except LeadBuyer.DoesNotExist:
            deals = 0
        else:
            deals = lb.deals()

        return self.render_to_response( {'ajax_chapter':True, 'form':self.form_class, 'expire':expire, 'deals':deals, 'chapter':chapter} )
    
    def form_invalid(self, form, chapter = None):
        context = self.get_context_data(form=form)
        if not chapter:
            chapter = Chapter.objects.all().order_by('name')[0]
        
        context.update(chapter=chapter)    
        return self.render_to_response(context)


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
            try:
                interest = Interest.objects.get(interest = custom)
            except Interest.DoesNotExist:
                interest = Interest( interest = custom, status = 'custom')
                interest.save()
            
        # Check if there are any existing deals
        chapter  = Chapter.objects.get(name = chapter)
        try:
            deal = Deal.objects.get( chapter = chapter, interest = interest )

        # If not create one
        except Deal.DoesNotExist:
            deal = Deal( chapter = chapter, interest = interest )
            deal.save()

        # Check the type of deal       
        if deal_type == 'Trial':
            expires = Expire.objects.filter( buyer = self.request.user,
                                             status = 'approved' 
                                           )
            
            if len ( expires ) >= settings.MAX_TRIALS:
                form._errors['deal_type'] = ErrorList(["Sorry. You already have an active trial"])
                
                return self.form_invalid(form, chapter)

            
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
            if deal_type ==  'Nonexclusive':
                cost = 20
                exclusive = False

            elif deal_type == 'Sponsored':
                cost = 0
                exclusive = True
                
                if len( deal.chapter.sponsors() ) >= settings.MAX_SPONSORS:
                    form._errors['deal_type'] = \
                        ErrorList(["Sorry. %s already has the maximum number of sponsors"% (deal.chapter.name,) ])
                    return self.form_invalid(form, chapter)

            
            
            cancel = Cancel( deal = deal,
                             cost = cost,
                             exclusive = exclusive,
                             buyer = self.request.user,
                             status = 'pending'
                            )
            cancel.save()
            mail_organizer( self.request.user, deal, cancel, deal_type )
        
        # If you already have payment details go to dashboard
        profile = self.request.user.get_profile()
        if profile.is_ready:
            return HttpResponseRedirect ( reverse('lb_dash')+"?state=apply" )
        else:
            return HttpResponseRedirect ( reverse('lb_payment') )

class DashView( TemplateView ):
    """
    Show the buyers dash board
    """
    template_name = 'leadb/lb_dash.html'
    
    def get_context_data(self, **kwargs):
        
        state = None
        if 'state' in self.request.GET:
            if self.request.GET['state'] == 'profile':
                state = 'Profile Updated'
            elif self.request.GET['state'] == 'payment':
                state = 'Payment Info Updated'
            elif self.request.GET['state'] == 'apply':
                state = 'Deal Pending'
            elif self.request.GET['state'] == 'budget':
                state = 'Budget Updated'
        
        buyer = self.request.user
        terms = Term.objects.filter(buyer = buyer).order_by('status')
          
        term_list = []
        total     = 0.0
        for term in terms:
            args = dict ( interest    = term.deal.interest.interest,
                          chapter     = term.deal.chapter,
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
            
            elif term.status == 'rejected':
                status = 'Rejected'
            
            else:
                child = term.get_child()
                if isinstance( child, Cancel ):
                    if term.exclusive:
                        status = 'Exclusive'
                    else:
                        status = 'Standard'
            
                elif isinstance( child, Expire ):
                    status = 'Trial'
        
            args.update(status = status)
            term_list.append(args)

        # Convert total to a string
        total = '%10.2f'%total
        total = dict(total = total)
        kwargs = dict( terms = term_list, total = total, state = state ) # {terms:terms, total:total, invoices:invoices }
        
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
    
    
class BillView( TemplateView ):
    template_name = 'leadb/lb_bills.html'
    
    def get_context_data(self):
        if 'invoice' in self.request.GET:
            invoice = Invoice.objects.get(pk=self.request.GET['invoice'])
            if invoice.user != self.request.user:
                return {}
        else:
            try:
                invoice = Invoice.objects.filter(user = self.request.user).latest('issued')
            except Invoice.DoesNotExist:
                return {}
        
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


class ChapterView( View ):
    def get(self, request, *arg, **kwargs ):
        
        # Explorer does not pass the parameters, so you have to check 
        if 'chapter' in request.GET  and 'term' in request.GET:            
            chapter     = Chapter.objects.get( pk = request.GET['chapter'] )
            term        = Term.objects.get( pk = request.GET['term'])
            connections = term.connections()
            return render_to_response( 'leadb/lb_organizer.html', 
                                       { 'chapter':chapter, 'term':term, 'connections':connections }, 
                                       context_instance=RequestContext(request) 
                                     )
            
        return HttpResponseRedirect(reverse('lb_dash'))



class PaymentBudgetView( MultipleFormsView ):
    """
    Treat the payment info and budget as two separate forms
    """
    template_name = 'leadb/lb_budget.html'
    form_classes  = {'payment':PaymentForm, 'budget':BudgetForm }
    
    
    def get(self, request, *args, **kwargs ):
  
        form_classes = self.get_form_classes()
        forms = self.get_forms(form_classes)
        
        forms['budget'] = self.budget_form()
        forms['payment'] = self.payment_form()

        return self.render_to_response(self.get_context_data(forms=forms))
    

    def post(self, request, *args, **kwargs):
        form_classes = self.get_form_classes()
        forms = self.get_forms(form_classes)
        
        # Figure out which for was submitted
        if 'budget' in request.GET:
            if forms['budget'].is_valid():
                return self.budget_form_valid(forms)
            else:
                forms['payment'] = self.payment_form()
                return self.forms_invalid(forms)
        
        elif 'payment' in request.GET:
            if forms['payment'].is_valid():
                return self.payment_form_valid(forms)
            else:
                forms['budget']= self.budget_form()
                return self.forms_invalid(forms)
            
    def budget_form(self):
        try:
            lb = LeadBuyer.objects.get(user = self.request.user)
        except LeadBuyer.DoesNotExist:
            budget = '$500.00'
        else:
            if lb.budget:
                budget = lb.budget
            else: 
                budget ='$500.00'
        form = BudgetForm(initial = {'budget':budget})
        return form


    def payment_form( self ):    
        user    = self.request.user
        profile = self.request.user.get_profile()
        try:
            authorize = Authorize.objects.get( user = user )
        except:
            ready = False
        else:
            ready = True if authorize.payment_profile else False
        
        initial = dict( ready = ready )
        if profile.address:
            if '^' in profile.address:
                billing = profile.address.split('^')
            else:
                billing = profile.address.split(',')
                 
            # Make sure there are no errant commas
            for i,bill in enumerate(billing):
                if ',' in bill:
                    billing[i] = bill.replace(',','')
            
            initial.update( dict (  address  = billing[0],
                                    city     = billing[1],
                                    state    = billing[2],
                                    zipcode  = billing[3]
                                 )
                          )
    
        return PaymentForm( initial = initial )


    def budget_form_valid(self, forms):
        budget      = forms['budget'].cleaned_data['budget']
        try:
            lb = LeadBuyer.objects.get( user = self.request.user )
        except LeadBuyer.DoesNotExist:
            forms['budget']._errors['budget'] = ErrorList(["Apply as leader first"])
            return self.forms_invalid(forms)
        
        money = re.compile('^\$?([1-9]{1}[0-9]{0,2}(\,[0-9]{3})*(\.[0-9]{0,2})?|[1-9]{1}[0-9]{0,}(\.[0-9]{0,2})?|0(\.[0-9]{0,2})?|(\.[0-9]{1,2})?)$')
        money = money.match(budget)
        if not money or budget == '':
            forms['budget']._errors['budget'] = ErrorList(["Not a valid dollar amount"])
            forms['payment'] = self.payment_form()
            return self.forms_invalid(forms)
        lb.budget = money.groups()[0]
        lb.save()
        
        return HttpResponseRedirect(reverse('lb_dash')+"?state=budget")
    
    def payment_form_valid(self, forms):
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

        # Check the expiration date
        expiration  = forms['payment'].cleaned_data['expire_year']+'-'+forms['payment'].cleaned_data['expire_month']
        
        expire = datetime.strptime(expiration,'%Y-%m').replace( day = 1 )
        if expire < datetime.today():
            forms['budget'] = self.budget_form()
            forms['payment']._errors['expire_year'] = ErrorList(["Date is in the past"])
            return self.forms_invalid(forms)
        
        # Get the card, expiration date, address and budget
        card_number = forms['payment'].cleaned_data[u'number']
        address     = forms['payment'].cleaned_data['address']
        city        = forms['payment'].cleaned_data['city']
        state       = forms['payment'].cleaned_data['state']
        zipcode     = forms['payment'].cleaned_data['zipcode']
         
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
        profile.address = address+'^'+city+'^'+state+'^'+zipcode
 
        # Create a Authorize.net CIM profile
        kw = dict ( card_number                 = card_number,
                    expiration_date             = unicode(expiration),
                    customer_id                 = unicode( authorize.customer_id ),
                    customer_profile_id         = unicode( authorize.profile_id ),
                    customer_payment_profile_id = unicode( authorize.payment_profile),     
                    profile_type                = CREDIT_CARD,
                    email                       = user.email,
                    validation_mode             = VALIDATION_LIVE
                  )
    
        kw.update(billing)
        
        # Initialize the API class
        cim_api = cim.Api( unicode(settings.AUTHORIZE['API_LOG_IN_ID']),
                           unicode(settings.AUTHORIZE['TRANSACTION_ID']) 
                         )
    
        try:
            #response = cim_api.update_profile( **kw )
            response = cim_api.update_payment_profile(**kw)
 
        except Exception, e:
            forms['budget'] = self.budget_form()
            forms['payment']._errors['card_number'] = ErrorList( ['Credit Card Authorization Failed'] )
            return self.forms_invalid(forms)
        
        # Check to see it if its OK
        result = response.messages.result_code.text_
        
        if result != 'Ok':
            forms['budget'] = self.budget_form()
            forms['payment']._errors['number'] = ErrorList( [response.messages.message.text.text_] )
            return self.forms_invalid(forms)
    
        return HttpResponseRedirect(reverse('lb_dash')+"?state=payment")

   
class PaymentView( FormView ):
    """
    Manage the payment and budget as one form initially
    """
    template_name = 'leadb/lb_payment.html'
    form_class    = PaymentBudgetForm
    
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
            if '^' in profile.address:
                billing = profile.address.split('^')
                
                return dict ( address = billing[0],
                              city    = billing[1],
                              state   = billing[2],
                              zipcode = billing[3],
                              budget  = budget
                            )
        
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
        profile.address = address+'^'+city+'^'+state+'^'+zipcode
 
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
        was_ready = profile.is_ready
        profile.is_ready = True
        profile.save()
        
        if not was_ready:
            return HttpResponseRedirect(reverse('lb_apply'))
        else:
            return HttpResponseRedirect(reverse('lb_dash')+"?state=payment")


@login_required
def term_state( request ):

    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        if term.owner() == request.user and 'status' in request.GET:
            status = request.GET['status']
            if status in TERM_STATUS:
                term.status = request.GET['status']
                term.save()
    return HttpResponseRedirect(reverse('lb_dash'))


@login_required
def cancel_term(request):
    # Cancel Terms of a Deal
    if request.method == 'GET' and 'term' in request.GET:
        term = Term.objects.get(pk = request.GET['term'])
        term.status = 'canceled'
        term.save()
        mail_organizer( request.user, term.deal, term, deal_type = 'cancel' )
    return HttpResponseRedirect(reverse('lb_dash'))



import logging
logger = logging.getLogger('django.request')

def ajax(request):
    """
    Handle Ajax requests from invitations
    """
    if 'chapter' in request.GET:
        chapter_name = request.GET['chapter']
        try:
            chapter = Chapter.objects.get( name = chapter_name )
        except Exception, e:
            msg = "%s for %s" % (str(e), chapter_name )
            logger.error(msg)
            chapter = None
        
    template = loader.get_template('leadb/lb_community.html')
    c = Context({'chapter':chapter})
    html = template.render(c)
    
    return HttpResponse(html, mimetype='text/html')