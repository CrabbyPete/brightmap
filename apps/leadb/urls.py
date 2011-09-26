from django.conf.urls.defaults  import *

urlpatterns = patterns('leadb.views',
    url(r'^lb_profile/$',            'lb_profile',            name='lb_profile'            ),
    url(r'^lb_payment/$',            'lb_payment',            name='lb_payment'            ),
    url(r'^lb_apply/$',              'lb_apply',              name='lb_apply'              ),
    url(r'^lb_dash/$',               'lb_dash',               name='lb_dash'               ),
)

