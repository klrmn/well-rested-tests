from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets


class Project(models.Model):

    name = models.CharField(max_length=200)


# Serializers define the API representation.
class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'url', 'name']


# ViewSets define the view behavior.
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
