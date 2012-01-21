from django.conf.urls.defaults import *

urlpatterns = patterns('social.views',
    url(r'^meetup/?$',              'meetup',         name = 'meetup_api'      ),
    url(r'^eventbrite/?$',          'eventbrite',     name = 'eventbrite_api'  ), 
)

