from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.shortcuts import get_object_or_404, render
import datetime

import permissions
from project import Project


class Case(models.Model):
    project = models.ForeignKey(Project)
    name = models.CharField(
        max_length=200, unique=True,
        verbose_name="Test Case Name")
    fixture = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def results(self):
        from result import Result
        return Result.objects.filter(case=self).order_by('-start_time')

    @property
    def passes(self):
        return self.results().filter(status='pass').count()

    @property
    def fails(self):
        return self.results().filter(status='fail').count()

    @property
    def xfails(self):
        return self.results().filter(status='xfail').count()

    @property
    def xpasses(self):
        return self.results().filter(status='xpass').count()

    @property
    def skips(self):
        return self.results().filter(status='skip').count()

    @property
    def average_pass_duration(self):
        tds = [result.duration for result in self.results().filter(status='pass')]
        if not tds:
            return None
        return sum(tds, datetime.timedelta(0)) / len(tds)

    @property
    def average_fail_duration(self):
        tds = [result.duration for result in
               self.results().filter(status='fail').exclude(duration=None)]
        if not tds:
            return None
        return sum(tds, datetime.timedelta(0)) / len(tds)

    @property
    def last_status(self):
        return self.results().first().status

    @property
    def last_week_status(self):
        # exists, inprogress, and skip don't count,
        # pass and xpass are count towards pass
        # fail, aborted, and xfail count towards fail
        cuttoff_time = datetime.datetime.now() - datetime.timedelta(days=7)
        results = self.results(
        ).exclude(status__in=['exists', 'inprogress', 'skip']
        ).exclude(start_time__lt=cuttoff_time)
        failed = len(results.filter(status__in=['fail', 'aborted', 'xfail']))
        if failed > (len(results) / 2):
            return 'fail'
        else:
            return 'pass'


    @property
    def max_duration(self):
        return max([result.duration for result in self.results()])


class CaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'fixture')


# Serializers define the API representation.
class CaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Case
        fields = ['id', 'url', 'project', 'name', 'fixture']


# ViewSets define the view behavior.
class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = (permissions.CreateOnly,)
    filter_fields = ('project', 'name', 'fixture')


def case(request, case_id):
    case = get_object_or_404(Case, pk=case_id)
    results = case.results().exclude(status='exists')
    passes = results.filter(status='pass').count()
    fails = results.filter(status='fail').count()
    xfails = results.filter(status='xfail').count()
    xpasses = results.filter(status='xpass').count()
    inprogress = results.filter(status='inprogress').count()
    skips = results.filter(status='skip').count()

    status = None
    if 'status' in request.GET:
        status = request.GET['status']
        results = results.filter(status=status)
    fixture = None
    if 'fixture' in request.GET:
        fixture = request.GET['fixture']
        if fixture == 'True':
            fixture = True
        else:
            fixture = False
        results = results.filter(case__fixture=fixture)
    return render(request, "wrt/case.html", {
        'status': status,
        'fixture': fixture,
        'case': case,
        'results': results,
        'passes': passes,
        'fails': fails,
        'xfails': xfails,
        'xpasses': xpasses,
        'inprogress': inprogress,
        'skip': skips,
    })
