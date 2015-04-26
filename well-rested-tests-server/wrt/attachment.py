from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py

from case_run import CaseRun


class Attachment(models.Model):
    case_run = models.ForeignKey(CaseRun)


class ImageAttachment(Attachment):
    file = models.ImageField(upload_to='screenshots',
                             null=False, editable=False)


class TextAttachment(Attachment):
    file = models.FileField(upload_to='text',
                            null=False, editable=False)
