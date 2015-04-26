from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets


class Case(models.Model):

    name = models.CharField(
        max_length=200, unique=True,
        verbose_name="Test Case Name")


# Serializers define the API representation.
class CaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'url', 'name']


# ViewSets define the view behavior.
class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
