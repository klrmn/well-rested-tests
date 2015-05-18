from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

import permissions
from project import Project


class Case(models.Model):
    # TODO: add a bunch of stats
    project = models.ForeignKey(Project)
    name = models.CharField(
        max_length=200, unique=True,
        verbose_name="Test Case Name")

    def project_name(self):
        return self.project.name


class CaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'project_name', 'name')


# Serializers define the API representation.
class CaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'url', 'project', 'name']


# ViewSets define the view behavior.
class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = (permissions.CreateOnly,)
