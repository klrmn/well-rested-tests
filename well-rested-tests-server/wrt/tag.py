from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

from project import Project
import permissions


class Tag(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name')


# Serializers define the API representation.
class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'url', 'project', 'name')


# ViewSets define the view behavior.
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.CreateOnly,)
    filter_fields = ('project',)
