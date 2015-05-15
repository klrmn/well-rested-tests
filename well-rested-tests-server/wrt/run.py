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
    # TODO: also, mark all related results aborted when
    # TODO: finishing run
    duration = models.DurationField(
        null=True, blank=True, editable=False)
    tags = models.ManyToManyField(Tag, blank=True)


# Serializers define the API representation.
class RunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Run
        fields = ('id', 'url', 'owner', 'project', 'start_time', 'end_time', 'tags')


# ViewSets define the view behavior.
class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    permission_classes = (permissions.OnlyAdminCanDelete,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
