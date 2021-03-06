from django.shortcuts               import  render_to_response
from django.template                import  RequestContext
from django.http                    import  HttpResponseRedirect
from django.core.urlresolvers       import  reverse

from base.models                    import Chapter, Invite
from base.forms                     import LoginForm
#from organizer.forms                import ServiceForm


def sponsor( request, slug ):
    if len(slug) <= 2:
        return HttpResponseRedirect(reverse('homepage'))
    
    try:
        chapter = Chapter.objects.get(slug = slug)
    except Chapter.DoesNotExist:
        return HttpResponseRedirect(reverse('homepage'))

    """ If you want to keep track uncomment, but every crawler will create an invite
    invite = Invite( chapter = chapter )
    invite.save()
    form = ServiceForm( initial = {'invite': str(invite.pk)} )
    data = dict(chapter = chapter, pop = True, invite = invite, form = form )
    """
    form = LoginForm(initial={'forgot':False})
    data = dict( chapter = chapter, pop = False, login = form  )
    return render_to_response( 'organizer/or_landing.html', 
                                data, 
                                context_instance=RequestContext(request) 
                              )
        
