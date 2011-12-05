from django.conf.urls.defaults  import *
from views                      import ( ChapterView, 
                                         EventbriteView, 
                                         DealView, 
                                         LeadBuyerView, 
                                         EventView,
                                         SurveyView,
                                         ConnectionView,
                                         TermView,
                                         ProfileView,
                                         InvoiceView
                                       )


urlpatterns = patterns('base.views',

    # default index
    url(r'^$',                      'homepage',                 name='homepage'             ),
    url(r'^login/$',                'login',                    name='login'                ),
    url(r'^logout/$',               'logout',                   name='logout'               ),
    url(r'^community/$',            'community',                name='community'            ),
    url(r'^about/$',                'about',                    name='about'                ),
    url(r'^terms/$',                'terms',                    name='terms'                ),
    url(r'^chapter/$',               ChapterView.as_view(),     name='chapter'              ),
    url(r'^eventbrite/$',            EventbriteView.as_view(),  name='eventbrite'           ),
    url(r'^deal/$',                  DealView.as_view(),        name='deal'                 ),
    url(r'^leadbuyer/$',             LeadBuyerView.as_view(),   name='leadbuyer'            ),
    url(r'^event/$',                 EventView.as_view(),       name='event'                ),
    url(r'^survey/$',                SurveyView.as_view(),      name='survey'               ),
    url(r'^connection/$',            ConnectionView.as_view(),  name='connection'           ),
    url(r'^term/$',                  TermView.as_view(),        name='term'                 ),
    url(r'^profile/$',               ProfileView.as_view(),     name='profile'              ),
    url(r'^invoice/$',               InvoiceView.as_view(),     name='invoice'              )
)
