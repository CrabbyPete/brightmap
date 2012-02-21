from django.contrib.auth.decorators import  login_required
from django.conf.urls.defaults  import patterns, url
from django.views.generic.simple import direct_to_template


from views                      import ( ChapterView, 
                                         EventbriteView, 
                                         DealView, 
                                         LeadBuyerView, 
                                         EventView,
                                         SurveyView,
                                         ConnectionView,
                                         TermView,
                                         ProfileView,
                                         InvoiceView,
                                         InterestView,
                                         CommissionView,
                                         LetterView
                                       )


urlpatterns = patterns('base.views',

    # default index
    url(r'^$',                  'homepage',                                 name='homepage'     ),
    url(r'^learn/$',            'learn',                                    name='learn'        ),
    url(r'^login/$',            'login',                                    name='login'        ),
    url(r'^forgot/$',           'forgot',                                   name='forgot'       ),
    url(r'^logout/$',           'logout',                                   name='logout'       ),
    url(r'^community/$',        'community',                                name='community'    ),
    url(r'^terms/$',            'terms',                                    name='terms'        ),
    url(r'^remind/$',           'remind',                                   name='remind'       ),
    url(r'^about/$',            'about',                                    name ='about'       ),
    url(r'^faq/$',              'faq',                                      name ='faq'         ),
    url(r'^interest/$',         login_required(InterestView.as_view()),     name='interest'     ),
    url(r'^chapter/$',          login_required(ChapterView.as_view()),      name='chapter'      ),
    url(r'^eventbrite/$',       login_required(EventbriteView.as_view()),   name='eventbrite'   ),
    url(r'^deal/$',             login_required(DealView.as_view()),         name='deal'         ),
    url(r'^leadbuyer/$',        login_required(LeadBuyerView.as_view()),    name='leadbuyer'    ),
    url(r'^event/$',            login_required(EventView.as_view()),        name='event'        ),
    url(r'^survey/$',           login_required(SurveyView.as_view()),       name='survey'       ),
    url(r'^connection/$',       login_required(ConnectionView.as_view()),   name='connection'   ),
    url(r'^term/$',             login_required(TermView.as_view()),         name='term'         ),
    url(r'^profile/$',          login_required(ProfileView.as_view()),      name='profile'      ),
    url(r'^invoice/$',          login_required(InvoiceView.as_view()),      name='invoice'      ),
    url(r'^commission/$',       login_required(CommissionView.as_view()),   name='commission'   ),
    url(r'^letter/$',           login_required(LetterView.as_view()),       name='letter'       ),
    url(r'^potential/$',        'potential',                                name ='potential'   )
)
