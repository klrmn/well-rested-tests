from django.contrib import admin

from .models import *
from .project import ProjectAdmin

admin.site.register(Project, ProjectAdmin)
admin.site.register(Case)
admin.site.register(Run)
admin.site.register(Result)
admin.site.register(Tag)
admin.site.register(TextAttachment)
admin.site.register(ImageAttachment)
