
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
                                            widget= forms.TextInput(attrs={'class':'supf','size':40})
                                         )

    password        = forms.CharField   ( max_length = 45,
                                            label = 'Password:',
                                            widget = forms.PasswordInput(attrs={'class':'supf','size':35},
                                                                         render_value = True              )
                                        )

    pass_confirm    = forms.CharField   ( max_length = 45,
                                            label = 'Confirm Password:',
                                            widget = forms.PasswordInput(attrs={'class':'supf','size':35},
                                                                         render_value = True              )
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


    phone           = USPhoneNumberField( required = False,
                                            label = 'Phone:',
                                            widget = forms.TextInput(attrs={'class':'supf','size':16})
                                         )


    address        = forms.RegexField  ( required = False,
                                            max_length = 45,
                                            label = 'Address:',
                                            regex=r"^[a-zA-Z0-9,' ']+$",
                                            error_message = ugettext_lazy("Only letters numbers and commas"),
                                            widget = forms.TextInput(attrs={'class':'row','size':40})
                                        )


    is_organizer   = forms.BooleanField( initial = True,
                                            label = 'Im an event organizer',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={'class':'row'})
                                        )


    is_attendee    = forms.BooleanField( initial = False,
                                            label = 'Im interested in sponsoring events',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={'class':'row'})
                                        )

    is_leadbuyer   = forms.BooleanField( initial = False,
                                            label = 'Im interested in buying leads',
                                            required = False,
                                            widget = forms.CheckboxInput(attrs={'class':'row'})
                                        )

class InterestForm(forms.Form):
    interests        = forms.CharField  ( required = False,
                                          widget = forms.Textarea(attrs={'cols':70, 'rows':10})
                                         )


class DealForm(forms.Form):

    organizer       = forms.IntegerField( required = False,
                                          widget=forms.HiddenInput() )

    interest        = forms.ChoiceField( choices=(),
                                         widget=forms.Select() )

    max_sell        = forms.IntegerField()

    add_terms       = forms.BooleanField( required = False,
                                          widget=forms.CheckboxInput(attrs={'class':'row'})    )


    def __init__(self, *args, **kwargs):
        super(DealForm, self).__init__(*args, **kwargs)
        self.fields['interest'].choices = [(i.interest,i.interest) for i in Interest.objects.all()]


TERM_CHOICES = [('Cancel','Until Cancel', forms.RadioSelect  ),
                ('Expire','Until Date',   forms.DateInput    ),
                ('Count' ,'Until Count',  forms.TextInput    )
               ]

class TermForm(forms.Form):
    cost            = forms.CharField( max_length = 10 )

    terms           = ChoiceWithOtherField( choices = TERM_CHOICES )

    buyers          = forms.ChoiceField( required = False,
                                         choices=(),
                                         label = 'Add Buyer',
                                         widget=forms.Select(attrs={})
                                       )


    def __init__(self, *args, **kwargs):
        super(TermForm, self).__init__(*args, **kwargs)
        self.fields['buyers'].choices = [('', 'None')]+[(i.user.email ,i.user.first_name + ' '+ i.user.last_name )
                                           for i in Profile.objects.filter(is_leadbuyer  = True)]



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
"""
class LeadForm (ModelForm):
    class Meta:
        model = Lead
        exclude = ('user')
"""

class ChapterForm(ModelForm):
    class Meta:
        model = Chapter

class LetterForm(ModelForm):
    class Meta:
        model = Letter

