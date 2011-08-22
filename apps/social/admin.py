from django.contrib import admin
from models         import *

admin.site.register(AuthToken)
admin.site.register(LinkedInProfile)
admin.site.register(TwitterProfile)
admin.site.register(FaceBookProfile)
admin.site.register(GoogleProfile)
admin.site.register(MeetupProfile)