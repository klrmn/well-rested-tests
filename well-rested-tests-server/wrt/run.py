from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.contrib.auth.models import User

from project import Project
from tag import Tag
import permissions


class Run(models.Model):
    project = models.ForeignKey(Project)
    owner = models.ForeignKey(User, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    # TODO: on test run end:
    # TODO:   mark all remaining inprogress results aborted
    duration = models.DurationField(
        null=True, blank=True, editable=False)
    status = models.CharField(null=True,
        max_length=12, blank=True,
        choices=(
            ('pass', 'pass'),
            ('fail', 'fail'),
            ('inprogress', 'inprogress'),
            ('aborted', 'aborted'),
        )
    )
    tests_run = models.IntegerField(default=0, blank=True)
    failures = models.IntegerField(default=0, blank=True)
    errors = models.IntegerField(default=0, blank=True)
    xpasses = models.IntegerField(default=0, blank=True)
    xfails = models.IntegerField(default=0, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return '%s %s (%s)' % (self.project, self.id, self.owner)

    def description(self):
        tags = [tag.name for tag in self.tags.all()]
        print(self.tags)
        return ' '.join(tags)


class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'duration', 'status', 'description',
                    'registered_tests', 'tests_run', 'failures', 'errors', 'xpasses', 'xfails')
    list_filter = ('project', 'owner', 'status', 'start_time')


# Serializers define the API representation.
class RunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Run
        fields = ('id', 'url', 'owner', 'project',
                  'start_time', 'end_time', 'duration', 'status',
                  'tests_run', 'failures', 'errors', 'xpasses', 'xfails',
                  'tags')


# ViewSets define the view behavior.
class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    permission_classes = (permissions.OnlyAdminCanDelete,)
