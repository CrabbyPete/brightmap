
from django.forms                           import ModelForm


#from radio                                  import ChoiceWithOtherField
from base.models                            import ( 
                                                     Invoice,
                                                     Commission,
                                                     Split
                                                   )


class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        exclude = ('user',)
 
        
class CommissionForm(ModelForm):
    class Meta:
        model = Commission


class SplitForm(ModelForm):
    class Meta:
        model = Split