from django.contrib import admin

from .models import *

admin.site.register(Project)
admin.site.register(Case)
admin.site.register(Run)
admin.site.register(CaseRun)
admin.site.register(RunEnvVar)
admin.site.register(TextAttachment)
admin.site.register(ImageAttachment)
