from django.contrib import admin
from models         import *



admin.site.register( Organization )

admin.site.register( Chapter )

admin.site.register( Deal )

admin.site.register( Event )

admin.site.register( LeadBuyer )

admin.site.register( Survey )

admin.site.register( Eventbrite )

admin.site.register( Invoice )

class ProfileAdmin(admin.ModelAdmin):
    ordering = ['user__email'] 
      
admin.site.register(Profile, ProfileAdmin)


class TermAdmin(admin.ModelAdmin):
    readonly_fields = ('modified',)
    
admin.site.register(Term, TermAdmin)


class ConnectionAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)
             
admin.site.register( Connection, ConnectionAdmin )


class AuthorizeAdmin(admin.ModelAdmin):
    ordering = ['user__last_name']
    
admin.site.register(Authorize, AuthorizeAdmin)