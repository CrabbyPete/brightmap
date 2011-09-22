from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$',          'base.views.homepage',  name='homepage'    ),
    (r'^base/',         include('base.urls')                       ),
    (r'^leadb/',        include('leadb.urls')                      ),
    (r'^social/',       include('social.urls')                     ),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')   ),
    url(r'^admin/',     include(admin.site.urls)                   ),
)

import os
import settings

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(os.path.dirname(__file__), "media")}),
   )
