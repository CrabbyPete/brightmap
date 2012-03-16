
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
                                                     Invoice,
                                                     Commission
                                                   )

class LoginForm(forms.Form):
    forgot          = forms.BooleanField( required = False,
                                          initial = False,
                                          widget = forms.HiddenInput(attrs={'id':'forgotten'})
                                        )
                                        
    username        = forms.EmailField  ( max_length = 45,
                                          widget = forms.TextInput( attrs={ 'value'  :"Email Address",
                                                                            'onfocus':"if(this.value == 'Email Address')this.value = ''",
                                                                            'onblur' :"if(this.value == '') this.value = 'Email Address'",
                                                                           } )
                                        )

    password        = forms.CharField   ( max_length = 45,
                                          required = False,
                                          widget = forms.PasswordInput( attrs={} )
                                        )

class UserForm( ModelForm ):
    class Meta:
        model = User
        fields = ('email','first_name','last_name')

class UserProfileForm( ModelForm ):     
    class Meta:         
        model = Profile 
        #exclude = ('user',)

class UserAndProfileForm( UserForm, UserProfileForm ):
    class Meta ( UserForm.Meta, UserProfileForm.Meta ):
        exclude = ('user',)

class InterestForm ( ModelForm ):
    class Meta:
        model = Interest
        exclude = ('occupation',)
    
    def clean(self):
        """ Override clean so you can edit interest which is unique """
        super(InterestForm, self).clean()
        self._validate_unique = False
        return self.cleaned_data
        
class DealForm( ModelForm ):
    class Meta:
        model = Deal
         
class LeadBuyerForm( ModelForm ):
    class Meta:
        model = LeadBuyer
        exclude = ('user',)
 
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
        exclude = ('user',)
        
class CommissionForm(ModelForm):
    class Meta:
        model = Commission
