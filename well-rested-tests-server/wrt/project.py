from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.shortcuts import render, get_object_or_404

import permissions


class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    def tags(self):
        from tag import Tag
        return Tag.objects.filter(project=self)

    def cases(self):
        from case import Case
        return Case.objects.filter(project=self)

    def runs(self):
        from run import Run
        return Run.objects.filter(project=self).order_by('-start_time')

    @property
    def reasons(self):
        reasons = set()
        for run in self.runs():
            reasons.update(run.reasons)
        return reasons


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


# Serializers define the API representation.
class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'url', 'name']


# ViewSets define the view behavior.
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = (permissions.AuthenticatedReadOnly,)


def projects(request):
    return render(request, 'wrt/projects.html', {
        'projects': Project.objects.all()
    })


def project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'wrt/project.html', {
        'project': project,
        'tags': project.tags(),
        'cases': project.cases(),
        'runs': project.runs(),
        'reasons': project.reasons,
        'passes': project.runs().filter(status='pass').count(),
        'fails': project.runs().filter(status='fail').count(),
        'in_progress': project.runs().filter(status='inprogress').count(),
        'aborted': project.runs().filter(status='aborted').count(),
    })
