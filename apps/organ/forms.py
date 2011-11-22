from django                                 import forms
from django.utils.translation               import ugettext_lazy

from base.models                            import Interest

class OrganizerForm( forms.Form ):
    email           = forms.EmailField  ( required = True,
                                            label = 'Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'size':40})
                                         )

    email_verify   = forms.EmailField  ( required = True,
                                            label = 'Confirm Email Address:',
                                            max_length = 60,
                                            widget= forms.TextInput(attrs={'size':40})
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
                                            widget = forms.TextInput(attrs={'size':40})
                                        )

    password        = forms.CharField   ( max_length = 45,
                                            label = 'Password',
                                            widget = forms.PasswordInput(attrs={'size':40}, render_value = True )
                                        )

    pass_confirm    = forms.CharField   ( max_length = 45,
                                            label = 'Confirm Password',
                                            widget = forms.PasswordInput(attrs={'size':40}, render_value = True )
                                        )


    organization    = forms.CharField  ( required = True,
                                            label = 'Organization Name',
                                            max_length =100,
                                            widget = forms.TextInput(attrs={'size':40})
                                        )

    chapter         = forms.CharField  ( required = False,
                                            label = 'Organization Chapter',
                                            max_length =100,
                                            widget = forms.TextInput(attrs={'size':40})
                                        )


    pay_pal         = forms.CharField   (
                                         required = False,
                                            label = 'Pay Pal Id',
                                            max_length = 255,
                                            widget = forms.TextInput(attrs={'size':40})
                                         )
    agree           = forms.BooleanField( initial = False,
                                          required = False,
                                          widget = forms.CheckboxInput(attrs={})
                                         )

class CatagoriesForm( forms.Form ):
    chapter     = forms.CharField ( required = True, widget = forms.HiddenInput() )
    
    standard    = forms.MultipleChoiceField( widget = forms.CheckboxSelectMultiple,choices=[] )
    
    other       = forms.MultipleChoiceField( required = False, widget = forms.CheckboxSelectMultiple,choices=[] )
    
    custom      = forms.BooleanField( initial  = False, 
                                      required = False, 
                                      widget   = forms.CheckboxInput 
                                    )
    
    field       = forms.CharField( required = False, max_length = 45 )

    def __init__(self, *args, **kwargs):
        super( CatagoriesForm, self).__init__(*args, **kwargs)
        self.fields['standard'].choices = [(i.interest,i.interest) for i in Interest.objects.filter(level = 1)]
        self.fields['other'].choices = [(i.interest,i.interest) for i in Interest.objects.filter(level = 2)]