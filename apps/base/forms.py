
from django                                 import forms
from django.utils.translation               import ugettext_lazy
from django.contrib.localflavor.us.forms    import USPhoneNumberField
from django.forms                           import ModelForm
from django.contrib.auth.models             import User 

#from radio                                  import ChoiceWithOtherField
from radio2                                 import ChoiceWithOtherField
from models                                 import ( Profile, 
                                                     LeadBuyer, 
                                                     Interest, 
                                                     Chapter, 
                                                     Letter,
                                                     Eventbrite, 
                                                     Deal, 
                                                     Event, 
                                                     Survey, 
                                                     Term, 
                                                     Connection,
                                                     Cancel, 
                                                     Expire,
                                                     Invoice
                                                   )

class LoginForm(forms.Form):
    username        = forms.EmailField  ( max_length = 45,
                                          widget = forms.TextInput( attrs={ 'value'  :"Email Address",
                                                                            'onfocus':"if(this.value == 'Email Address')this.value = ''",
                                                                            'onblur' :"if(this.value == '') this.value = 'Email Address'",
                                                                           } )
                                        )

    password        = forms.CharField   ( max_length = 45,
                                          widget = forms.PasswordInput( attrs={} )
                                        )

class SignUpForm(forms.Form):

    email           = forms.EmailField  ( required = True,
                                            label = 'Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'size':40})
                                         )

    first_name      = forms.RegexField  ( required = False,
                                            label = 'First Name:',
                                            max_length =45, regex=r'^[a-zA-Z]+$',
                                            error_message = ugettext_lazy("Only letters are allowed; 3 letters at least"),
                                            widget = forms.TextInput(attrs={'size':40})
                                        )

    last_name       = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Last Name:',
                                            regex=r'^[a-zA-Z]+$',
                                            error_message = ugettext_lazy("Only letters are allowed"),
                                            widget = forms.TextInput(attrs={'size':40})
                                        )


    phone           = USPhoneNumberField( required = False,
                                            label = 'Phone:',
                                            widget = forms.TextInput(attrs={'size':16})
                                         )


    address        = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Address:',
                                            regex=r"^[a-zA-Z0-9,' ']+$",
                                            error_message = ugettext_lazy("Only letters numbers and commas"),
                                            widget = forms.TextInput(attrs={'size':40})
                                        )


    is_organizer   = forms.BooleanField( initial = False,
                                            label = 'Im an event organizer',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={})
                                        )


    is_attendee    = forms.BooleanField( initial = False,
                                            label = 'Im interested in sponsoring events',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={})
                                        )

    is_leadbuyer   = forms.BooleanField( initial = True,
                                            label = 'Im interested in buying leads',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={})
                                        )




class InterestForm(forms.Form):
    interests        = forms.ChoiceField( choices=(),
                                          label = 'Interest',
                                          widget=forms.Select(attrs={})
                                        )

    def __init__(self, *args, **kwargs):
        super(InterestForm, self).__init__(*args, **kwargs)
        self.fields['interests'].choices = [(i.interest,i.interest) for i in Interest.objects.all()]

class ProfileForm( SignUpForm ):

    password        = forms.CharField   ( max_length = 45,
                                            label = 'Password',
                                            widget = forms.PasswordInput(attrs={'size':35}, render_value = True )
                                        )

    pass_confirm    = forms.CharField   ( max_length = 45,
                                            label = 'Confirm Password',
                                            widget = forms.PasswordInput(attrs={'size':35}, render_value = True )

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

    website         = forms.URLField     ( required = False,
                                          max_length = 100,
                                          label = 'Company Web Site:',
                                          widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )

    newsletter       = forms.BooleanField( initial = False,
                                            label = 'Subscribe to newsletter',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={'class':'row'})
                                         )





DEAL_CHOICES = (('Exclusive','Exclusive ($50.00 per Introduction)'),
                ('Nonexclusive','Nonexclusive ($20.00 per Introduction'),
                ('Trial' ,'Trial (free for 1 month)')
               )


class BuyDealForm(forms.Form):

    chapter          = forms.CharField  ( required = False,
                                            label = 'Community:',
                                            max_length =45,
                                            widget = forms.TextInput(attrs={'size':40})
                                        )
    interest         = forms.CharField  ( required = False,
                                            label = 'Interest:',
                                            max_length =45,
                                            widget = forms.TextInput(attrs={'size':40})
                                        )

    deal_type        = forms.ChoiceField( required = False,
                                            choices=DEAL_CHOICES,
                                            label = 'Deal Type:',
                                            widget=forms.RadioSelect(attrs={})
                                       )


class UserForm( ModelForm ):
    class Meta:
        model = User
        fields = ('email','first_name','last_name')

class UserProfileForm( ModelForm ):     
    class Meta:         
        model = Profile 
        exclude = ('user',)

class UserAndProfileForm( UserForm, UserProfileForm ):
    class Meta ( UserForm.Meta, UserProfileForm.Meta ):
        exclude = ('user',)

class DealForm( ModelForm ):
    class Meta:
        model = Deal
         
class LeadBuyerForm( ModelForm ):
    class Meta:
        model = LeadBuyer
 
class ChapterForm(ModelForm):
    class Meta:
        model = Chapter
    
class EventbriteForm(ModelForm):
    class Meta:
        model = Eventbrite
        
class LetterForm(ModelForm):
    class Meta:
        model = Letter
        
class EventForm(ModelForm):
    class Meta:
        model = Event
               
class SurveyForm(ModelForm):
    class Meta:
        model = Survey
        
class ConnectionForm(ModelForm):
    class Meta:
        model = Connection
        fields = ( 'status',)
               
class TermForm(ModelForm):
    class Meta:
        model = Term

class CancelForm(ModelForm):
    class Meta:
        model = Cancel
        
class ExpireForm(ModelForm):
    class Meta:
        model = Expire

class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice