from django.conf.urls.defaults      import  patterns, url
from views                          import  SignUp, Apply, Payment

urlpatterns = patterns('leadb.views',
    url(r'^lb_signup/$',              SignUp.as_view(),       name='lb_signup'             ),
    url(r'^lb_profile/$',            'lb_profile',            name='lb_profile'            ),
    url(r'^lb_payment/$',             Payment.as_view(),      name='lb_payment'            ),
    url(r'^lb_apply/$',               Apply.as_view(),        name='lb_apply'              ),
    url(r'^lb_dash/$',               'lb_dash',               name='lb_dash'               ),
    url(r'^lb_details/$',            'lb_details',            name='lb_details'            ),
)

