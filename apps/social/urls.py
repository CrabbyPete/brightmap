from django.conf.urls.defaults import *

urlpatterns = patterns('social.views',
    url(r'^linkedin/?$',            'linkedin',      name = 'linkedin'     ),
    url(r'^facebook/?$',            'facebook',      name = 'facebook'     ),
    url(r'^twitter/?$',             'twitter',       name = 'twitter'      ),
    url(r'^google/?$',              'google',        name = 'google'       ),
    url(r'^meetup/?$',              'meetup',        name = 'meetup'       ),
    url(r'^gmail/?$',               'gmail',         name = 'gmail'        ),
    url(r'^eventbrite/?$',          'eventbrite',    name = 'eventbrite'   ), 
)

