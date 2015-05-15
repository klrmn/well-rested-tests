from django.contrib import admin

from .models import *
from .project import ProjectAdmin
from .tag import TagAdmin
from .run import RunAdmin
from .case import CaseAdmin
from  .result import ResultAdmin

admin.site.register(Project, ProjectAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Run, RunAdmin)
admin.site.register(Result, ResultAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(TextAttachment)
admin.site.register(ImageAttachment)
