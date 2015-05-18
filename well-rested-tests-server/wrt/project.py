from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

import permissions


class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


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
