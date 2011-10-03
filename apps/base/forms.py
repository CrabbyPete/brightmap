
from django                                 import forms
from django.utils.translation               import ugettext_lazy
from django.contrib.localflavor.us.forms    import USPhoneNumberField
from django.forms                           import ModelForm

#from radio                                  import ChoiceWithOtherField
from radio2                                 import ChoiceWithOtherField
from models                                 import *

class LoginForm(forms.Form):
    username        = forms.EmailField   ( max_length = 45,
                                            widget = forms.TextInput(attrs={'class':'txtBox1','size':19, 'id':'user',
                                            'value':"Email Address",
                                            'onfocus':"if(this.value == 'Email Address')this.value = ''",
                                            'onblur' :"if(this.value == '') this.value = 'User Name or Email Address'"}
                                        )

                                        )
    password        = forms.CharField   ( max_length = 45,
                                            widget = forms.PasswordInput(attrs={'class':'txtBox1','size':19,
                                            'value':"Password",
                                            'onfocus':"if(this.value == 'Password')this.value = ''",
                                            'onblur' :"if(this.value == '') this.value = 'Password'"})
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


TERM_CHOICES = [('Cancel','Until Cancel', forms.RadioSelect  ),
                ('Expire','Until Date',   forms.DateInput    ),
                ('Count' ,'Until Count',  forms.TextInput    ),
                ('Budget','Under Budget', forms.TextInput    ),
               ]

class DealForm(forms.Form):

    organizer       = forms.IntegerField( required = False,
                                          widget=forms.HiddenInput() )

    interest        = forms.ChoiceField( choices=(),
                                         widget=forms.Select() )

    exclusive       = forms.BooleanField( required = False,
                                          widget=forms.CheckboxInput(attrs={})
                                        )

    cost            = forms.CharField( max_length = 10 )

    terms           = ChoiceWithOtherField( choices = TERM_CHOICES )

    buyers          = forms.ChoiceField( required = False,
                                         choices=(),
                                         label = 'Add Buyer',
                                         widget=forms.Select(attrs={})
                                       )

    def __init__(self, *args, **kwargs):
        super(DealForm, self).__init__(*args, **kwargs)
        self.fields['interest'].choices = [(i.interest,i.interest) for i in Interest.objects.all()]
        self.fields['buyers'].choices = [('', 'None')]+[(i.user.email ,i.user.first_name + ' '+ i.user.last_name )
                                           for i in Profile.objects.filter(is_leadbuyer  = True)]



class BuyerForm(forms.Form):
    email           = forms.EmailField  ( required = True,
                                            label = 'Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'size':40})
                                         )


    email_verify    = forms.EmailField  ( required = True,
                                            label = 'Verify Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'size':40})
                                         )
    
    phone           = USPhoneNumberField( required = False,
                                            label = 'Phone:',
                                            widget = forms.TextInput(attrs={})
                                         )


    first_name      = forms.RegexField  ( required = True,
                                            label = 'First Name:',
                                            max_length =45, regex=r'^[a-zA-Z]+$',
                                            error_message = ugettext_lazy("Only letters are allowed; 3 letters at least"),
                                            widget = forms.TextInput(attrs={})
                                        )

    last_name       = forms.RegexField  ( required = True,
                                            max_length = 45,
                                            label = 'Last Name:',
                                            regex=r'^[a-zA-Z]+$',
                                            error_message = ugettext_lazy("Only letters are allowed"),
                                            widget = forms.TextInput(attrs={})
                                        )

    password        = forms.CharField   ( required = True,
                                            max_length = 45,
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
                                            widget = forms.TextInput(attrs={'size':40})
                                        )

    company         = forms.CharField  ( required = False,
                                            label = 'Company:',
                                            max_length =45,
                                            widget = forms.TextInput(attrs={'size':40})
                                        )


    address        = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Address:',
                                            regex=r"^[a-zA-Z0-9,' ']+$",
                                            error_message = ugettext_lazy("Only letters numbers and commas"),
                                            widget = forms.TextInput(attrs={'size':40})
                                        )
    website         = forms.URLField     ( required = False,
                                          max_length = 100,
                                          label = 'Company Web Site:',
                                          widget = forms.TextInput(attrs={'size':40})
                                        )

    linkedin        = forms.URLField ( required = False,
                                          max_length = 100,
                                          label = 'LinkedIn Web Site',
                                          widget = forms.TextInput(attrs={'size':40})
                                        )
    twitter         = forms.URLField ( required = False,
                                          max_length = 100,
                                          label = 'Twitter Web Site',
                                          widget = forms.TextInput(attrs={'size':40})
                                        )

    agree           = forms.BooleanField( initial = False,
                                          required = False,
                                          widget = forms.CheckboxInput(attrs={'class':'supf'})
                                         )


class BuyersForm( forms.Form):
    buyers        = forms.ChoiceField( required = False,
                                       choices=(),
                                       widget=forms.Select( attrs={'class':'row'}) )
    term          = forms.IntegerField( required = False, widget=forms.HiddenInput() )

    def __init__(self, *args, **kwargs):
        super(BuyersForm, self).__init__(*args, **kwargs)
        self.fields['buyers'].choices = [('', 'None')]+[(i.user.email ,i.user.first_name + ' '+ i.user.last_name )
                                           for i in Profile.objects.filter(is_leadbuyer  = True)]

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

class LeadBuyerForm(ModelForm):
    class Meta:
        model = LeadBuyer
        exclude = ('user','letter')


class ChapterForm(ModelForm):
    class Meta:
        model = Chapter

class LetterForm(ModelForm):
    class Meta:
        model = Letter

