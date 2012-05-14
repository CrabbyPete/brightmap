# Python imports
import logging
logger = logging.getLogger('mail')

from datetime                       import datetime, timedelta, time


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
from django.contrib.auth.decorators import  login_required

# Local imports
import settings


from base.models                    import (Chapter, Invoice, Commission)
from base.mail                      import Mail
                                        


# Import for authorize
from authorize                      import cim
from authorize.gen_xml              import VALIDATION_TEST, AUTH_ONLY
from authorize.responses            import AuthorizeError, _cim_response_codes

# Import accounting functions
from cron.accounting                import invoice_user, bill_user, notify_user, pay_commissions
from paypal                         import pay_commission


from forms                          import InvoiceForm, CommissionForm

@login_required
def months( request ):
    months = []
    for invoice in Invoice.objects.filter().order_by('first_day').reverse():
        if not invoice.title in months:
            months.append( invoice.title )
    
    c = Context({'months':months})         
    return render_to_response('accounting/months.html', c, context_instance=RequestContext(request))
    
class InvoiceView ( FormView):
    template_name   = 'accounting/invoice.html'
    form_class      = InvoiceForm
    
    def get(self, request, *args, **kwargs):
        if 'invoice' in request.GET:
            invoice = Invoice.objects.get(pk = request.GET['invoice'])
           
            # Update to the latest invoice
            updated_invoice = invoice_user ( invoice.user, invoice.first_day, invoice.last_day )
            if updated_invoice:
                invoice = updated_invoice
            
            connections = invoice.connections()
            form = InvoiceForm(instance = invoice)
        
            return self.render_to_response( {'form':form, 'invoice':invoice, 'connections':connections} )
        
        total       = 0.0
        income      = 0.0
        commissions = 0.0
        
        if 'title' in request.GET:
            invoices = Invoice.objects.filter(title = request.GET['title'])
            for invoice in invoices:
                if invoice.status == 'paid':
                    income += float(invoice.cost) - float(invoice.credit)
                    for com in invoice.commissions():
                        if com.status == 'paid':
                            commissions += float(com.cost)
                
                
        else:
            invoices = Invoice.objects.all().order_by('issued').reverse()
        
        total = income - commissions
        return self.render_to_response( {'income'     :income, 
                                         'commissions':commissions,
                                         'total'      :total,
                                         'split'      : 0.25 * total,
                                         'invoices'   :invoices} )
        
         
    def form_valid(self, form ):
        invoice = Invoice.objects.get( pk = self.request.GET['invoice'] )
        if invoice.status == 'pending' and invoice.cost > 0:
            invoice = bill_user ( invoice )
            pay_commissions( invoice )
            if invoice.status == 'paid':
                notify_user( invoice )
        
        else:
            invoice.status = form.cleaned_data['status']
            invoice.credit = form.cleaned_data['credit']
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
        cost    = form.cleaned_data['cost']
        #chapter = form.cleaned_data['chapter']
        commission = Commission.objects.get( pk = self.request.GET['commission'] )
        paypal = commission.chapter.paypal
        if paypal:
            memo = ' %s commission payment for leads generated for %s %s'%(commission.chapter.name,
                                                                              commission.invoice.user.first_name,
                                                                              commission.invoice.user.last_name 
                                                                          )
            if  pay_commission( paypal, cost, memo ):
                commission.status = 'paid'
                commission.save()
        return HttpResponseRedirect(reverse('commission'))
            

