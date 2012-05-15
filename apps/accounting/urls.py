from django.contrib.auth.decorators     import  login_required
from django.conf.urls.defaults          import patterns, url

from views import InvoiceView, CommissionView, SplitView

urlpatterns = patterns('accounting.views',
    url(r'^months/$',            'months',                                  name='months'       ),
    url(r'^invoice/$',          login_required(InvoiceView.as_view()),      name='invoice'      ),
    url(r'^commission/$',       login_required(CommissionView.as_view()),   name='commission'   ),
    url(r'split/$',             'split',                                    name='split'        ),
    url(r'splitview/$',         login_required(SplitView.as_view()),        name='splitview'    )

)
