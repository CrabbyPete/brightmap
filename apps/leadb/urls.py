from django.contrib.auth.decorators import  login_required
from django.conf.urls.defaults      import  patterns, url
from views                          import  SignUpView, ApplyView, PaymentView, PaymentBudgetView, DashView, BillView, ChapterView

urlpatterns = patterns('leadb.views',
    url(r'^lb_signup/$',                    SignUpView.as_view(),           name='lb_signup'      ),
    url(r'^lb_payment/$',   login_required( PaymentView.as_view() ),        name='lb_payment'     ),
    url(r'^lb_payment2/$',  login_required( PaymentBudgetView.as_view() ),  name='lb_payment2'     ),
    url(r'^lb_apply/$',     login_required( ApplyView.as_view()   ),        name='lb_apply'       ),
    url(r'^lb_dash/$',      login_required( DashView.as_view()    ),        name='lb_dash'        ),
    url(r'^lb_bill/$',      login_required( BillView.as_view()    ),        name='lb_bill'        ),
    url(r'^lb_chapter/$',   login_required( ChapterView.as_view() ),        name='lb_chapter'     ),    
    url(r'^lb_cancel/$',                    'cancel_term',                  name='lb_cancel'      ),
    url(r'^lb_term_state/$',                'term_state',                   name='lb_term_state'  ),  
)

