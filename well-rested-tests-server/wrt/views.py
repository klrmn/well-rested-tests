from django.http import HttpResponse
from django.conf.urls import url

from project import project, projects
from case import case
from run import run
from tag import tag


def index(request):
    return HttpResponse('Hello, world. You\'re at the wrt index.\n'
                        '<a href="/projects">Go to Projects</a>')


urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'projects/*$', projects, name='projects'),
    url(r'project/(?P<project_id>[0-9]+)/$', project, name='project'),
    url(r'case/(?P<case_id>[0-9]+)/$', case, name='case'),
    url(r'run/(?P<run_id>[0-9]+)/$', run, name='run'),
    url(r'tag/(?P<tag_id>[0-9]+)/$', tag, name='tag'),
]
