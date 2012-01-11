from django.contrib.auth.decorators import  login_required
from django.conf.urls.defaults      import  patterns, url

from views                          import  ( SignUpView, CategoryView )
                                             
urlpatterns = patterns('organ.views',
    url(r'^signup/$',       SignUpView.as_view(),                       name='or_signup'    ),
    url(r'^category/$',     login_required( CategoryView.as_view()),    name='or_category'  ),
    url(r'^setup/$',        'setup',                                    name='or_setup'     ),
    url(r'^dash/$',         'dashboard',                                name='or_dash'      ),
    url(r'^leadb/$',        'leadb',                                    name='or_leadb'     ),
    url(r'^status/$',       'status',                                   name='or_status'    ),
    url(r'^events/$',       'events',                                   name='or_events'    ),
)

