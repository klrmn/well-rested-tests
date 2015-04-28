from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

from run import Run
import permissions


class RunEnvVar(models.Model):
    run = models.ForeignKey(Run)
    name = models.CharField(
        max_length=200, verbose_name="Environmental Variable")
    value = models.CharField(max_length=200)


# Serializers define the API representation.
class RunEnvVarSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RunEnvVar
        fields = ('id', 'url', 'run', 'name', 'value')


# ViewSets define the view behavior.
class RunEnvVarViewSet(viewsets.ModelViewSet):
    queryset = RunEnvVar.objects.all()
    serializer_class = RunEnvVarSerializer
    permission_classes = (permissions.CreateOnly,)
