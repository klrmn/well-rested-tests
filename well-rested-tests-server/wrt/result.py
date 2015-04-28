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
    # post with just case and run to specify that a test has been
    # discovered for this test run
    case = models.ForeignKey(Case)
    run = models.ForeignKey(Run)
    owner = models.ForeignKey(User, null=True, blank=True)
    # TODO: populate start_time by fake 'start' api
    start_time = models.DateTimeField(
        'Start Datetime', null=True)
    # TODO: populate end_time, result, reason, and duration by fake api
    end_time = models.DateTimeField(
        'End Datetime', null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    status = models.CharField(null=True,
        max_length=12, default="exists", blank=True,
        choices=(
            ('exists', 'exists'),
            ('pass', 'pass'),
            ('fail', 'fail'),
            ('skip', 'skip'),
            ('unknown', 'unknown'),
            ('inprogress', 'inprogress'),
            ('aborted', 'aborted'),
        )
    )
    reason = models.TextField(null=True, blank=True)


# Serializers define the API representation.
class ResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Result
        fields = ('id', 'url', 'case', 'run', 'start_time',
                  'end_time', 'duration', 'status', 'reason')


# ViewSets define the view behavior.
class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = (permissions.OnlyAdminCanDelete,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
