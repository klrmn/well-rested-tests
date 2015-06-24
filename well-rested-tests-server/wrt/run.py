from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404

from project import Project
from tag import Tag
import permissions


class Run(models.Model):
    project = models.ForeignKey(Project)
    owner = models.ForeignKey(User, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    # TODO: on test run end:
    # TODO:   mark all remaining inprogress results aborted
    status = models.CharField(null=True,
        max_length=12, blank=True,
        choices=(
            ('pass', 'pass'),
            ('fail', 'fail'),
            ('inprogress', 'inprogress'),
            ('aborted', 'aborted'),
        )
    )
    tags = models.ManyToManyField(Tag, blank=True)

    @property
    def duration(self):
        if self.start_time and self.end_time and self.status != 'inprogress':
            return self.end_time - self.start_time
        return None

    def results(self):
        from result import Result
        return Result.objects.filter(run=self).order_by('-start_time')

    def __str__(self):
        return '%s %s (%s)' % (self.project, self.id, self.owner)

    @property
    def reasons(self):
        rsns = []
        for result in self.results():
            rsns.append(result.reason)
        return set(rsns)

    # counts
    @property
    def tests_run(self):
        return self.results().exclude(status='exists').count()

    @property
    def passes(self):
        return self.passed_tests().count()

    @property
    def failures(self):
        return self.failed_tests().count()

    @property
    def xpasses(self):
        return self.xpassed_tests().count()

    @property
    def xfails(self):
        return self.xfailed_tests().count()

    @property
    def skips(self):
        return self.skipped_tests().count()

    def failed_tests(self):
        return self.results().filter(status='fail')

    def passed_tests(self):
        return self.results().filter(status='pass')

    def xfailed_tests(self):
        return self.results().filter(status='xfail')

    def xpassed_tests(self):
        return self.results().filter(status='xpass')

    def skipped_tests(self):
        return self.results().filter(status='skip')

    def description(self):
        # used to show tags in the admin interface
        tags = [tag.name for tag in self.tags.all()]
        print(self.tags)
        return ' '.join(tags)


class RunAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_time', 'end_time', 'duration', 'status', 'description',
                    'results', 'tests_run', 'failures', 'xpasses', 'xfails')
    list_filter = ('project', 'owner', 'status', 'start_time')


# Serializers define the API representation.
class RunSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Run
        fields = ('id', 'url', 'owner', 'project',
                  'start_time', 'end_time', 'duration', 'status',
                  'tests_run', 'failures', 'xpasses', 'xfails',
                  'skips', 'tags')


# ViewSets define the view behavior.
class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    permission_classes = (permissions.OnlyAdminCanDelete,)
    # don't try to filter by tags, they can't be made into a query string
    filter_fields = ('project', 'status')


def run(request, run_id):
    run = get_object_or_404(Run, pk=run_id)
    results = run.results().filter(case__fixture=False)
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
    return render(request, 'wrt/run.html', {
        'status': status,
        'run': run,
        'tags': run.tags.all(),
        'results': results,
        'passes': passes,
        'fails': fails,
        'xfails': xfails,
        'xpasses': xpasses,
        'inprogress': inprogress,
        'skip': skips,
    })
