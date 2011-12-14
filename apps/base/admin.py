from django.contrib import admin
from models         import *

class ProfileAdmin(admin.ModelAdmin):
    ordering = ['user__email'] 
      
admin.site.register(Profile, ProfileAdmin)

admin.site.register(Organization)

admin.site.register(Chapter)

admin.site.register(Deal)

admin.site.register(Term)

admin.site.register(Event)

admin.site.register(Connection)

admin.site.register(LeadBuyer)


class AuthorizeAdmin(admin.ModelAdmin):
    ordering = ['user__last_name']
    
admin.site.register(Authorize, AuthorizeAdmin)