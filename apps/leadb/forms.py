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
    email           = forms.EmailField  ( required = True,
                                            label = 'Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'class':'row','size':40})
                                         )

    email_verify   = forms.EmailField  ( required = True,
                                            label = 'Confirm Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'class':'row','size':40})
                                         )

    phone           = USPhoneNumberField( required = False,
                                            label = 'Phone:',
                                            widget = forms.TextInput(attrs={'class':'row','size':16})
                                         )


    first_name      = forms.RegexField  ( required = False,
                                            label = 'First Name:',
                                            max_length =45, regex=r'^[a-zA-Z\40]+$',
                                            error_message = ugettext_lazy("Only letters spaces are allowed; 3 letters at least"),
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    last_name       = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Last Name:',
                                            regex=r'^[a-zA-Z\40]+$',
                                            error_message = ugettext_lazy("Only letters and spaces are allowed"),
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    password        = forms.CharField   ( max_length = 45,
                                            label = 'Password',
                                            widget = forms.PasswordInput(attrs={'size':40}, render_value = True )
                                        )

    pass_confirm    = forms.CharField   ( max_length = 45,
                                            label = 'Confirm Password',
                                            widget = forms.PasswordInput(attrs={'size':40}, render_value = True )
                                        )


    title          = forms.CharField  ( required = False,
                                            label = 'Title:',
                                            max_length =45,
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    company         = forms.CharField  ( required = False,
                                            label = 'Company:',
                                            max_length =45,
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )


    address        = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Address:',
                                            regex=r"^[a-zA-Z0-9,' ']+$",
                                            error_message = ugettext_lazy("Only letters numbers and commas"),
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )
    website         = forms.URLField     ( required = False,
                                          max_length = 100,
                                          label = 'Company Web Site:',
                                          widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    linkedin        = forms.URLField ( required = False,
                                          max_length = 100,
                                          label = 'LinkedIn Web Site',
                                          widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )
    twitter         = forms.URLField ( required = False,
                                          max_length = 100,
                                          label = 'Twitter Web Site',
                                          widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    agree           = forms.BooleanField( initial = False,
                                          required = False,
                                          widget = forms.CheckboxInput(attrs={'class':'supf'})
                                         )

DEAL_CHOICES = [('Sponsored','Sponsored (free)'),
                ('Exclusive','Exclusive ($50.00 per Introduction)'),
                ('Nonexclusive','Nonexclusive ($20.00 per Introduction'),
                ('Trial' ,'Trial (free for 1 month)')
               ]


APPLY_CHOICES = [('Non-Standard', 'Non-Standard', forms.Select     ),
                 ('Custom'      , 'Custom',       forms.TextInput  ),
                ]

class ApplyForm(forms.Form):
    chapter          = forms.ChoiceField( choices=(),
                                          widget=forms.Select(attrs={'class':"selectbox"})
                                        )

    
    interest         = forms.ChoiceField( required = False,
                                          choices=(),
                                          widget=forms.Select(attrs={'class':"selectbox"}) 
                                        )

    #other            = ChoiceWithOtherField( choices = APPLY_CHOICES )
    
    
    custom           = forms.CharField( max_length = 100,
                                        widget = forms.TextInput()
                                      )
  
    deal_type        = forms.ChoiceField( required = False,
                                          choices=DEAL_CHOICES,
                                          widget=forms.RadioSelect(attrs={'class':"selectbox"})
                                        )
 
    def __init__(self, *args, **kwargs):
        super(ApplyForm, self).__init__(*args, **kwargs)
        self.fields['interest'].choices = [(i.interest,i.interest) for i in Interest.objects.all()]
        self.fields['chapter'].choices = [(i.name,i.name) for i in Chapter.objects.all()]



MONTH_CHOICES = [ (1,'January'),(2,'February'),(3,'March'),(4,'April'),(5,'May'),(6,'June'),
                  (7,'July'),(8,'August'),(9,'September'),(10,'October'),(11,'November'),(12,'December')
                ]

BUDGET_CHOICES = [ ('No Budget', 'No Budget' ),
                   ('Budget'   , 'Budget' )
                 ] 



class PaymentForm(forms.Form):
    number          = CreditCardField()
    
    expire_month    = forms.ChoiceField( choices = MONTH_CHOICES,
                                         widget = forms.Select(attrs={'class':"selectbox1"})
                                       )
    
    expire_year     = forms.ChoiceField( choices = [],
                                         widget = forms.Select(attrs={'class':"selectbox1"})
                                       )
    
    address         = forms.CharField   ( max_length = 100,
                                          widget = forms.TextInput()
                                        )
    
    city            = forms.CharField   ( max_length = 100,
                                          widget = forms.TextInput()
                                        )
    
    state           = forms.CharField   ( max_length = 40,
                                          widget = forms.TextInput(attrs={'id':"inputext4"})  
                                        )

    zipcode         = USZipCodeField    ( required = False,
                                          widget= forms.TextInput(attrs={'id':"inputext4"})
                                        )
    
    
    budget          = ChoiceWithOtherField ( choices = BUDGET_CHOICES )

  
    def __init__(self,*args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['expire_year'].choices =  [(yr,yr) for yr in xrange(date.today().year,date.today().year + 15)]