from django.conf.urls.defaults  import *

urlpatterns = patterns('base.views',

    # default index
    url(r'^$',                      'homepage',             name='homepage'             ),
    url(r'^login/$',                'login',                name='login'                ),
    url(r'^signup/$',               'signup',               name='signup'               ),
    url(r'^logout/$',               'logout',               name='logout'               ),
    url(r'^community/$',            'community',            name='community'            ),
    url(r'^edit_profile/$',         'edit_profile',         name='edit_profile'         ),
    url(r'^edit_chapter/$',         'edit_chapter',         name='edit_chapter'         ),
    url(r'^show_chapter/$',         'show_chapter',         name='show_chapter'         ),
    url(r'^edit_interest/$',        'edit_interest',        name='edit_interest'        ),
    url(r'^edit_deal/$',            'edit_deal',            name='edit_deal'            ),
    url(r'^show_deal/$',            'show_deal',            name='show_deal'            ),
    url(r'^show_deals/$',           'show_deals',           name='show_deals'           ),
    url(r'^cancel_term/$',          'cancel_term',          name='cancel_term'          ),
    url(r'^show_event/$',           'show_event',           name='show_event'           ),
    url(r'^show_events/$',          'show_events',          name='show_events'          ),
    url(r'^show_buyer/$',           'show_buyer',           name='show_buyer'           ),
    url(r'^add_buyer/$',            'add_buyer',            name='add_buyer'            ),
    url(r'^edit_buyer/$',           'edit_buyer',           name='edit_buyer'           ),
    url(r'^edit_letter/$',          'edit_letter',          name='edit_letter'          ),
    url(r'^show_connection/$',      'show_connection',      name='show_connection'      ),
    url(r'^show_survey/$',          'show_survey',          name='show_survey'          ),
    url(r'^show_available_deals/$', 'show_available_deals', name='show_available_deals' ),
    url(r'^buy_deal/$',             'buy_deal',             name='buy_deal'             ),
)
