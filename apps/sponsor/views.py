from django.shortcuts               import  render_to_response
from django.template                import  RequestContext

from base.models                    import Chapter

def sponsor(request, slug ):
    chapter = Chapter.objects.get(slug = slug)
    data = dict(chapter = chapter, pop = False )
    return render_to_response( 'organizer/or_landing.html', 
                                data, 
                                context_instance=RequestContext(request) 
                              )
        
