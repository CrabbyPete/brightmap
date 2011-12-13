from django.contrib.auth.decorators import  login_required
from django.conf.urls.defaults      import  patterns, url

from views                          import  SignUp, Category, setup, dashboard, status

urlpatterns = patterns('organ/views',
    url(r'^signup/$',       SignUp.as_view(),                   name='or_signup'            ),
    url(r'^category/$',     login_required( Category.as_view()),name='or_category'          ),
    url(r'^setup/$',        setup,                              name='or_setup'             ),
    url(r'^dash/$',         dashboard,                          name='or_dash'              ),
    url(r'^status/$',       status,                             name='or_status'            ),
)

