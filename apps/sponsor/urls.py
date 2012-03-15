from django.conf.urls.defaults          import patterns, url


urlpatterns = patterns('sponsor.views',
    url(r'^(?P<slug>[-\w\d]+)',                 'sponsor',                                  name='sponsor'     ),
)
