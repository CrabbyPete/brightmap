from piston.handler         import BaseHandler
from base.models            import Chapter, Organization, Event


class OrganizationHandler( BaseHandler ):
    allowed_methods = ('GET',)
    model = Organization
    
    def read(self, request):
        if 'name' in request.GET:
            name = request.GET['name']
            organization = Organization.objects.get(name = name)
            return organization
        
        
class ChapterHandler( BaseHandler ):
    allowed_methods = ('GET',)
    model = Chapter   

    def read( self, request ):
        if 'name' in request.GET:
            name = request.GET['name']
            chapter = Chapter.objects.filter( name = name )
            return chapter
        elif 'id' in request.GET:
            chapter_id = request.GET['id']
            chapter = Chapter.objects.get(pk = chapter_id)
            return chapter
         
        return Chapter.objects.all()
                 
class EventHandler( BaseHandler ):
    allowed_methods = ('GET',)
    model = Event
    
    def read(self, request):
        if 'chapter' in request.GET:
            chapter = request.GET['chapter']
            return Event.objects.filter( chapter = chapter )
    
    