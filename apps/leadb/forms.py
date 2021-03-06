# Python imports
from datetime                               import date

# Django imports
from django                                 import forms
from django.utils.translation               import ugettext_lazy
from django.contrib.localflavor.us.forms    import USPhoneNumberField, USZipCodeField

# Local imports
from base.models                            import  Interest, Chapter
from base.radio                             import  ChoiceWithOtherField 
from creditfields                           import  CreditCardField

class BuyerForm(forms.Form):
    invite          = forms.CharField   ( required = False, widget = forms.HiddenInput() )
    
    email           = forms.EmailField  ( required = True,
                                          max_length = 60,
                                          widget= forms.TextInput()
                                        )
    """
    email_verify   = forms.EmailField  ( required = True,
                                         max_length = 60,
                                         widget= forms.TextInput()
                                       )
    """
    phone           = USPhoneNumberField( required = False,
                                          label = 'Phone:',
                                          widget = forms.TextInput(attrs={'class':'row','size':16})
                                         )


    first_name      = forms.RegexField  ( required = True,
                                          max_length = 45, 
                                          regex=r'^[a-zA-Z\40]+$',
                                          error_message = ugettext_lazy("Only letters spaces are allowed; 3 letters at least"),
                                          widget = forms.TextInput()
                                        )

    last_name       = forms.RegexField  ( required = True,
                                          max_length = 45,
                                          regex=r'^[a-zA-Z\40]+$',
                                          error_message = ugettext_lazy("Only letters and spaces are allowed"),
                                          widget = forms.TextInput()
                                        )

    password        = forms.CharField   ( max_length = 45,
                                          label = 'Password',
                                          widget = forms.PasswordInput(attrs={'size':40}, render_value = True )
                                        )
    """
    pass_confirm    = forms.CharField   ( max_length = 45,
                                          widget = forms.PasswordInput(attrs={'size':40}, render_value = True )
                                        )
    """

    title          = forms.CharField   ( required = False,
                                         max_length = 45,
                                         widget = forms.TextInput()
                                       )

    company         = forms.CharField  ( required = False,
                                         max_length = 45,
                                         widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )


    address        = forms.RegexField  ( required = False,
                                         max_length = 45,
                                         regex=r"^[a-zA-Z0-9,' ']+$",
                                         error_message = ugettext_lazy("Only letters numbers and commas"),
                                         widget = forms.TextInput(attrs={'size':40})
                                        )
    
    website         = forms.URLField    ( required = False,
                                          max_length = 100,
                                          widget = forms.TextInput(attrs={'size':40})
                                        )

    linkedin        = forms.URLField    ( required = False,
                                          max_length = 100,
                                          widget = forms.TextInput()
                                        )
    
    twitter         = forms.CharField ( required = False,
                                        max_length = 100,
                                        widget = forms.TextInput()
                                      )

    agree           = forms.BooleanField( initial = False,
                                          required = False,
                                          widget = forms.CheckboxInput()
                                        )
    
    

DEAL_CHOICES = [
                ('Nonexclusive','Standard ($20.00 per introduction)'),
                ('Sponsored','I am already a sponsor of this organization'),
                ('Trial' ,'Apply for Trial (1 month or 20 free leads )')
               ]

DEAL_CHOICES2 =[
                ('Nonexclusive','Standard ($20.00 per introduction)'),
                ('Sponsored','I am already a sponsor of this organization')
               ]

"""
STANDARD_CHOICES = [(i.interest,i.interest) for i in Interest.objects.filter(status='standard')]

APPLY_CHOICES = [('Standard', 'Standard', forms.Select(choices = STANDARD_CHOICES)     ),
                 ('Custom'  , 'Custom',   forms.TextInput  ),
                ]
"""

class ApplyForm(forms.Form):
    chapter          = forms.ChoiceField( choices=(),
                                          widget=forms.Select(attrs={'class':"selectbox",
                                                                     'onchange':'loadChapter(this.form)'
                                                                     })
                                        )

    
    interest         = forms.ChoiceField( required = False,
                                          choices=(),
                                          widget=forms.Select(attrs={'class':"selectbox"}) 
                                        )

    """
    other            = ChoiceWithOtherField( required = False,
                                             choices = APPLY_CHOICES 
                                           )
    
    """
    custom           = forms.CharField( required = True,
                                        max_length = 100,
                                        widget = forms.TextInput()
                                      )
 
    deal_type        = forms.ChoiceField( required = True,
                                          initial ='Nonexclusive',
                                          choices = DEAL_CHOICES,
                                          widget=forms.RadioSelect(attrs={'class':"termscode"})
                                        )
 
    def __init__(self, *args, **kwargs):
        super(ApplyForm, self).__init__(*args, **kwargs)
        self.fields['interest'].choices = [(i.interest,i.interest) 
                                           for i in Interest.objects.filter(status='standard').order_by('interest')
                                          ]
        self.fields['chapter'].choices = [(i.name,i.name) for i in Chapter.objects.all().order_by('name') if i.configured()]



MONTH_CHOICES = [ ('01','January'),('02','February'),('03','March'),    ('04','April'),  ('05','May'),     ('06','June'),
                  ('07','July'),   ('08','August'),  ('09','September'),('10','October'),('11','November'),('12','December')
                ]


""" Radio2
BUDGET_CHOICES = [('Budget'   , 'Budget',    forms.TextInput() ), 
                  ('No Budget', 'No Budget', forms.RadioSelect )
                 ] 

"""
BUDGET_CHOICES = [ 
                  ('No Budget', 'Zero budget (for free trials and sponsorships only)'),
                  ('Budget'   , 'Budget' )
                 ] 

class PaymentForm(forms.Form):
    """
    Credit card form
    """

    # This field is used internally whan the form is split.
    ready           = forms.BooleanField(  required = False,
                                           initial = False,
                                           widget = forms.HiddenInput()
                                        )
    

    number          = CreditCardField()
    
    expire_month    = forms.ChoiceField( choices = MONTH_CHOICES,
                                         widget = forms.Select(attrs={'class':"selectbox1"})
                                       )
    
    expire_year     = forms.ChoiceField( choices = [],
                                         widget = forms.Select(attrs={'class':"selectbox1"})
                                       )
    
    
    address         = forms.CharField   ( max_length = 100,
                                          widget = forms.TextInput(attrs={'id':"inputext1"})
                                        )
    
    address2         = forms.CharField  ( required = False,
                                          max_length = 100,
                                          widget = forms.TextInput(attrs={'id':"inputext1"})
                                        )
    
    city            = forms.CharField   ( max_length = 100,
                                          widget = forms.TextInput(attrs={'id':"inputext1"})
                                        )
    
    state           = forms.CharField   ( max_length = 2,
                                          widget = forms.TextInput(attrs={'class':"stateabbr"})  
                                        )

    zipcode         = USZipCodeField    ( required = False,
                                          widget= forms.TextInput(attrs={'class':"eightythree"})
                                        )
    
    def __init__(self,*args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['expire_year'].choices =  [(yr,yr) for yr in xrange(date.today().year,date.today().year + 8)]
        

class BudgetForm( forms.Form ):
    """
    Account Budget form
    """
    budget          =  forms.CharField  ( max_length = 45,
                                          widget = forms.TextInput
                                        )
    
class PaymentBudgetForm( PaymentForm, BudgetForm ):
    """
    Combination of PaymentForm and BudgetForm
    """
    cc_ready        =  forms.BooleanField( required = False, 
                                           initial  = False 
                                         )
    
