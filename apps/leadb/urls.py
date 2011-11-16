from django.contrib.auth.decorators import  login_required
from django.conf.urls.defaults      import  patterns, url
from views                          import  SignUp, Apply, Payment, Dash, Bill

urlpatterns = patterns('leadb.views',
    url(r'^lb_signup/$',                    SignUp.as_view(),       name='lb_signup'      ),
    url(r'^lb_payment/$',   login_required( Payment.as_view() ),    name='lb_payment'     ),
    url(r'^lb_apply/$',     login_required( Apply.as_view()   ),    name='lb_apply'       ),
    url(r'^lb_dash/$',      login_required( Dash.as_view()    ),    name='lb_dash'        ),
    url(r'^lb_bills/$',     login_required( Bill.as_view()    ),    name='lb_bill'        ),
    url(r'^lb_cancel/$',                    'cancel_term',          name='lb_cancel'      )
)

