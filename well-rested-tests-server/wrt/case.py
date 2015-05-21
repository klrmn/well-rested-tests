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

    def __str__(self):
        return self.name

    def tests(self):
        from result import Result
        return Result.objects.filter(case=self)

    def failed_tests(self):
        return self.tests.filter(status='fail')

    def passed_tests(self):
        return self.tests.filter(status='pass')

    def xfailed_tests(self):
        return self.tests.filter(status='xfail')

    def xpassed_tests(self):
        return self.tests.filter(status='xpass')

    def skipped_tests(self):
        return self.tests.filter(status='skip')

class CaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name')


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
    filter_fields = ('project',)
