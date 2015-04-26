from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py

from run import Run
from case import Case


class CaseRun(models.Model):
    case = models.ForeignKey(Case)
    run = models.ForeignKey(Run)
    start_time = models.DateTimeField(
        'Start Datetime', null=True)
    end_time = models.DateTimeField(
        'End Datetime', null=True, auto_now=True)
    duration = models.DurationField(null=True)
    result = models.CharField(
        max_length=12, default="exists", blank=False,
        choices=[
            ('exists', 'exists'),
            ('pass', 'pass'),
            ('fail', 'fail'),
            ('skip', 'skip'),
            ('unknown', 'unknown'),
            ('inprogress', 'inprogress')
        ]
    )
    reason = models.TextField(null=True)
