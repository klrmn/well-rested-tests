from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.contrib.auth.models import User

from project import Project
import permissions


class Run(models.Model):
    project = models.ForeignKey(Project)
    # TODO: figure out a way to make user self-fill-in
    owner = models.ForeignKey(User, null=True, blank=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    # TODO: fill this in when we know the run is done
    # TODO: might be a fake api not backed by a model
    # TODO: also, mark all related results aborted when
    # TODO: finishing run
    duration = models.DurationField(
        null=True, blank=True, editable=False)


# Serializers define the API representation.
class RunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Run
        fields = ('id', 'url', 'user', 'project', 'start_time', 'end_time')


# ViewSets define the view behavior.
class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    permission_classes = (permissions.OnlyAdminCanDelete,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
