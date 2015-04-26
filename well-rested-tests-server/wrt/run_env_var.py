from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py

from run import Run


class RunEnvVar(models.Model):
    run = models.ForeignKey(Run)
    name = models.CharField(
        max_length=200, verbose_name="Environmental Variable")
    value = models.CharField(max_length=200)
