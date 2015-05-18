from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.contrib.auth.models import User

from run import Run
from case import Case
import permissions


class Result(models.Model):
    case = models.ForeignKey(Case)
    run = models.ForeignKey(Run)
    owner = models.ForeignKey(User)
    start_time = models.DateTimeField(
        'Start Datetime', null=True, blank=True)
    end_time = models.DateTimeField(
        'End Datetime', null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    status = models.CharField(null=True,
        max_length=12, default="exists", blank=True,
        choices=(
            ('exists', 'exists'),
            ('pass', 'pass'),
            ('xpass', 'xpass'),
            ('xfail', 'xfail'),
            ('fail', 'fail'),
            ('skip', 'skip'),
            ('unknown', 'unknown'),
            ('inprogress', 'inprogress'),
            ('aborted', 'aborted'),
        )
    )
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return '%s %s' % (self.case.name, self.run.id)

    def project(self):
        return self.case.project


class ResultAdmin(admin.ModelAdmin):
    list_display = ('__str__',
                    'start_time', 'end_time', 'duration', 'status', 'reason')
    list_filter = ('run', 'case', 'status', 'reason', 'start_time')


# Serializers define the API representation.
class ResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Result
        fields = ('id', 'url', 'case', 'run', 'start_time', 'owner',
                  'end_time', 'duration', 'status', 'reason')


# ViewSets define the view behavior.
class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = (permissions.OnlyAdminCanDelete,)
