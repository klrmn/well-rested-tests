from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.shortcuts import get_object_or_404, render

from project import Project
import permissions


class Tag(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

    @property
    def passes(self):
        return self.run_set.filter(status='pass').count()

    @property
    def fails(self):
        return self.run_set.filter(status='fail').count()

    @property
    def inprogress(self):
        return self.run_set.filter(status='inprogress').count()

    @property
    def aborted(self):
        return self.run_set.filter(status='aborted').count()


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name')


# Serializers define the API representation.
class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'url', 'project', 'name')


# ViewSets define the view behavior.
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.CreateOnly,)
    filter_fields = ('project',)


def tag(request, tag_id):
    tag = get_object_or_404(Tag, pk=tag_id)
    runs = tag.run_set.all()
    status = None
    if 'status' in request.GET:
        status = request.GET['status']
        runs = runs.filter(status=status)
    return render(request, 'wrt/tag.html', {
        'tag': tag,
        'status': status,
        'runs': runs,
        'passes': runs.filter(status='pass').count(),
        'fails': runs.filter(status='fail').count(),
        'in_progress': runs.filter(status='inprogress').count(),
        'aborted': runs.filter(status='aborted').count(),
    })
