
from django                                 import forms
from django.utils.translation               import ugettext_lazy
from django.contrib.localflavor.us.forms    import USPhoneNumberField
from django.forms                           import ModelForm


#from radio                                  import ChoiceWithOtherField
from base.models                            import ( 
                                                     Invoice,
                                                     Commission
                                                   )


class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        exclude = ('user',)
        
class CommissionForm(ModelForm):
    class Meta:
        model = Commission
