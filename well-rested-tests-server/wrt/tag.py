from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.shortcuts import get_object_or_404, render

from project import Project
from case import Case
import permissions


class Tag(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=200, null=False, blank=False)
    value = models.CharField(max_length=200, null=False, blank=False)

    class Meta:
        unique_together = ('project', 'name', 'value')

    def __str__(self):
        return '%s %s' % (self.name, self.value)

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
    list_display = ('id', 'project', 'name', 'value')


# Serializers define the API representation.
class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'url', 'project', 'name', 'value')


# ViewSets define the view behavior.
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.CreateOnly,)
    filter_fields = ('project', 'name', 'value')


def tag(request, tag_id):
    tg = get_object_or_404(Tag, pk=tag_id)
    runs = tg.run_set.all()
    status = None
    if 'status' in request.GET:
        status = request.GET['status']
        runs = runs.filter(status=status)
    cases = Case.objects.filter(project=tg.project, fixture=False)
    from result import Result
    results = []
    for case in cases:
        row = (case, [])
        for run in runs:
            try:
                row[1].append(Result.objects.get(run=run, case=case))
            except (IndexError, Result.DoesNotExist):
                row[1].append(None)
        results.append(row)
    return render(request, 'wrt/tag.html', {
        'tag': tg,
        'status': status,
        'runs': runs,
        'results': results,
        'passes': runs.filter(status='pass').count(),
        'fails': runs.filter(status='fail').count(),
        'in_progress': runs.filter(status='inprogress').count(),
        'aborted': runs.filter(status='aborted').count(),
    })
