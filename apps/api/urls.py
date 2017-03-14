from django.conf.urls.defaults      import  patterns, url
from piston.resource                import Resource
from handlers                       import ChapterHandler, OrganizationHandler, EventHandler

chapter       = Resource(ChapterHandler)
organization  = Resource(OrganizationHandler)
event         = Resource(EventHandler)

urlpatterns = patterns('',
    url( r'^chapter/$',         chapter,      { 'emitter_format': 'json' }),
    url( r'^organization/$',    organization, { 'emitter_format': 'json' }),
    url( r'^event/$',           event,        { 'emitter_format': 'json' }),
)

