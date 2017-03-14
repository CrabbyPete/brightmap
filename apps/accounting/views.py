# Python imports
import logging
logger = logging.getLogger('mail')

# Django imports
from django.http                    import  HttpResponseRedirect
from django.shortcuts               import  render_to_response
from django.template                import  RequestContext
from django.views.decorators.csrf   import  csrf_protect
from django.core.urlresolvers       import  reverse
from django.views.generic.edit      import  FormView
from django.template                import  Context
from django.contrib.auth.decorators import  login_required



from base.models                    import ( Chapter, Invoice, Commission, Split )
from base.mail                      import Mail
                                        


# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes

# Import locals
from cron.accountant                import ( invoice_user, 
                                             bill_user, 
                                             notify_user,
                                             make_commissions 
                                            )

from paypal                         import pay_user
from forms                          import InvoiceForm, CommissionForm, SplitForm

@login_required
def months( request ):
    months = []
    for invoice in Invoice.objects.filter().order_by('first_day').reverse():
        if not invoice.title in months:
            months.append( invoice.title )
    
    c = Context({'months':months})         
    return render_to_response('accounting/months.html', c, context_instance=RequestContext(request))

def calc_split(invoices):
        income      = 0.0
        commissions = 0.0
        
        for invoice in invoices:
            if invoice.status == 'paid':
                income += float(invoice.cost) - float(invoice.credit)
                for com in invoice.commissions():
                    if com.status == 'paid':
                            commissions += float(com.cost)
        return income, commissions

@login_required
def split( request ):
    if request.GET and 'title' in request.GET:
        invoices = Invoice.objects.filter(title = request.GET['title'], status = 'paid')
        income, commissions = calc_split( invoices )
        total = income - commissions
        cost  = .25 * total
        memo  = request.GET['title']
        
        try:
            pete = Split.objects.get( payee = 'pete.douma@gmail.com',
                                       memo  = memo
                                     )
        except Split.DoesNotExist:
            pete  = Split( memo = request.GET['title'], 
                           cost = cost,
                           payee = 'pete.douma@gmail.com',
                           status = 'pending'
                         )
        else:
            pete.cost = cost
        pete.save()
        
        try:
            graham = Split.objects.get( payee = 'graham@ultralightstartups.com',
                                       memo  = memo
                                     )
        except Split.DoesNotExist:
            graham = Split( memo = request.GET['title'],
                            cost = cost,
                            payee = 'graham@ultralightstartups.com',
                            status = 'pending',
                          )
        else:
            graham.cost = cost
        
        graham.save()
    
    splits = Split.objects.all()
    c = Context({'splits':splits})         
    return render_to_response('accounting/split.html', c, context_instance=RequestContext(request))
        
class InvoiceView ( FormView ):
    template_name   = 'accounting/invoice.html'
    form_class      = InvoiceForm
    
    def get(self, request, *args, **kwargs):
        context = {}
        if 'invoice' in request.GET:
            invoice = Invoice.objects.get(pk = request.GET['invoice'])
           
            # Update to the latest invoice
            updated_invoice = invoice_user ( invoice.user, invoice.first_day, invoice.last_day )
            if updated_invoice:
                invoice = updated_invoice
            
            connections = invoice.connections()
            form = InvoiceForm(instance = invoice)
        
            context = {'form':form, 'invoice':invoice, 'connections':connections}
 
        
        
        if 'title' in request.GET:
            invoices = Invoice.objects.filter(title = request.GET['title'])
            income, commissions = calc_split( invoices )
    
            context.update(
                           title = request.GET['title'], 
                           income = income, 
                           commissions = commissions,
                           total = income - commissions,
                           split = .25 * (income - commissions),
                           invoices = invoices
                           )
 
        return self.render_to_response( context )
        
         
    def form_valid(self, form ):
        invoice = Invoice.objects.get( pk = self.request.GET['invoice'] )
        
        # If any thing changed add it first
        invoice.status = form.cleaned_data['status']
        invoice.credit = form.cleaned_data['credit']
        
        # Collect pending invoices
        if invoice.status == 'pending' and invoice.cost > 0:
            invoice = bill_user ( invoice )
            
            # Calculate commissions
            make_commissions( invoice )
            if invoice.status == 'paid':
                notify_user( invoice )
  
        invoice.save()
        return HttpResponseRedirect(reverse('months'))

class CommissionView ( FormView ):
    template_name   = 'admin/commission.html'
    form_class      = CommissionForm

    def get(self, request, *argv, **kwargs ):
        if 'commission' in request.GET:
            commission = Commission.objects.get(pk = request.GET['commission'])
            form = CommissionForm( instance = commission )
            return self.render_to_response({'form':form, 'commission':commission})
        
        if 'chapter' in request.GET:
            chapter = Chapter.objects.get(pk = request.GET['chapter'])
            commissions = Commission.objects.filter( chapter = chapter )
        
        elif 'title' in request.GET:
            invoices = Invoice.objects.filter(title = request.GET['title'])
            commissions = []
            for invoice in invoices:
                commissions.extend( invoice.commissions() )
  
        return self.render_to_response( {'commissions':commissions} )
    
    def form_valid(self, form ): 
        cost     = form.cleaned_data['cost']
        #chapter = form.cleaned_data['chapter']
        
        commission = Commission.objects.get( pk = self.request.GET['commission'] )
        paypal = commission.chapter.paypal
        if paypal:
            memo = ' %s commission payment for leads generated for %s %s'%(commission.chapter.name,
                                                                              commission.invoice.user.first_name,
                                                                              commission.invoice.user.last_name 
                                                                          )
            if  pay_user( paypal, cost, memo ):
                commission.status = 'paid'
                commission.save()
        
        return HttpResponseRedirect( reverse('commission')+'?title='+str(commission.invoice.title) )
            

class SplitView ( FormView ):
    template_name   = 'accounting/split.html'
    form_class      = SplitForm
    
    def get(self, request, *args, **kwargs):
        if 'split' in request.GET:
            split = Split.objects.get(pk = request.GET['split'])
            form = SplitForm( instance = split )
        return self.render_to_response( {'form':form, 'split':split}  )
    
    def form_valid(self, form, *args, **kwargs ):
        split = Split.objects.get(pk = self.request.GET['split'] )
        
        status = form.cleaned_data['status']
        memo   = form.cleaned_data['memo']
        cost   = form.cleaned_data['cost']
        paypal = form.cleaned_data['payee']
        
        if status == 'pending':
            if  pay_user( paypal, cost, memo ):
                split.status = 'paid'
        split.save()
            
        return HttpResponseRedirect(reverse('months'))

