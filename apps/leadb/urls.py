from django.conf.urls.defaults      import  patterns, url
from views                          import  SignUp, Apply, Payment, Dash, Bill

urlpatterns = patterns('leadb.views',
    url(r'^lb_signup/$',              SignUp.as_view(),       name='lb_signup'             ),
    url(r'^lb_payment/$',             Payment.as_view(),      name='lb_payment'            ),
    url(r'^lb_apply/$',               Apply.as_view(),        name='lb_apply'              ),
    url(r'^lb_dash/$',                Dash.as_view(),         name='lb_dash'               ),
    url(r'^lb_bills',                 Bill.as_view(),         name='lb_bill'               ),
)

