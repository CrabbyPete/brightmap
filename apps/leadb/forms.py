from django                                 import forms
from django.utils.translation               import ugettext_lazy
from django.contrib.localflavor.us.forms    import USPhoneNumberField

from base.models                            import *

class BuyerForm(forms.Form):
    email           = forms.EmailField  ( required = True,
                                            label = 'Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'class':'row','size':40})
                                         )


    phone           = USPhoneNumberField( required = False,
                                            label = 'Phone:',
                                            widget = forms.TextInput(attrs={'class':'row','size':16})
                                         )


    first_name      = forms.RegexField  ( required = False,
                                            label = 'First Name:',
                                            max_length =45, regex=r'^[a-zA-Z]+$',
                                            error_message = ugettext_lazy("Only letters are allowed; 3 letters at least"),
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    last_name       = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Last Name:',
                                            regex=r'^[a-zA-Z]+$',
                                            error_message = ugettext_lazy("Only letters are allowed"),
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

DEAL_CHOICES = (('Sponsored','Sponsored (free)'),
                ('Exclusive','Exclusive ($50.00 per Introduction)'),
                ('Nonexclusive','Nonexclusive ($20.00 per Introduction'),
                ('Trial' ,'Trial (free for 1 month)')
               )

class ApplyForm(forms.Form):
    chapter          = forms.ChoiceField( choices=(),
                                            widget=forms.Select()
                                        )

    interest         = forms.ChoiceField( choices=(),
                                         widget=forms.Select() )

    deal_type        = forms.ChoiceField( required = False,
                                            choices=DEAL_CHOICES,
                                            widget=forms.RadioSelect(attrs={})
                                       )
    suggest          = forms.CharField  ( required = False,
                                            label = 'Suggestion',
                                            max_length =45,
                                            widget = forms.TextInput(attrs={'size':40})
                                        )

    def __init__(self, *args, **kwargs):
        super(ApplyForm, self).__init__(*args, **kwargs)
        self.fields['interest'].choices = [(i.interest,i.interest) for i in Interest.objects.all()]
        self.fields['chapter'].choices = [(i.name,i.name) for i in Chapter.objects.all()]


class BudgetForm(forms.Form):
    budget          = forms.DecimalField( label = 'Monthly Budget')


from fields import CreditCardField, CreditCardExpiryField, CreditCardCVV2Field, CountryField

class CIMPaymentForm(forms.Form):
    card_number     = CreditCardField(label="Credit Card Number")
    
    expiration_date = CreditCardExpiryField(label="Expiration Date")
    
    card_code       = CreditCardCVV2Field( required = False,
                                           label="Card Security Code")
    
    billing_addr    = forms.CharField   ( required = False,
                                          max_length = 255,
                                          widget = forms.TextInput(attrs={
                                          'value':"street, city, state zipcode",
                                          'onfocus':"if(this.value == 'street, city, state zipcode') this.value = ''",
                                          'onblur' :"if(this.value == '') this.value = 'street, city, state zipcode'"
                                          })
                                         )
    
    budget          = forms.CharField   ( required = False,
                                          max_length = 40,
                                          widget = forms.TextInput(attrs={})
                                         )
 
