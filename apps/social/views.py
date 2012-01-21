from django.core.urlresolvers       import  reverse
from django.http                    import  HttpResponseRedirect
from django.template                import  RequestContext
from django.shortcuts               import  render_to_response


from oauth2                         import  EventbriteAPI, MeetUpAPI
from settings                       import  EVENTBRITE, MEETUP, SITE_BASE


meetup_api      = MeetUpAPI( MEETUP['API_KEY'], MEETUP['APP_SECRET'] )
eventbrite_api  = EventbriteAPI( EVENTBRITE['API_KEY'], EVENTBRITE['APP_SECRET']  )


def eventbrite( request ):
    if 'code' in request.GET:
        eventbrite_api.callback( request )
    
    elif not eventbrite_api.is_registered( request.user  ):
        url = eventbrite_api.register( request.user, SITE_BASE + reverse('eventbrite_api') )
        return HttpResponseRedirect(url)
    
    return HttpResponseRedirect(reverse('homepage'))

def meetup( request ):
    if 'code' in request.GET:
        meetup_api.callback( request )
        return render_to_response('landing.html',{}, context_instance=RequestContext(request) )
    
    elif not meetup_api.is_registered( request.user ):
        url = meetup_api.register( request.user, SITE_BASE + reverse('meetup_api') )
        return HttpResponseRedirect(url)
    
    return render_to_response('landing.html',{}, context_instance=RequestContext(request) )
        
    pass