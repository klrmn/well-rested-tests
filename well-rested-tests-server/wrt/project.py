from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py


class Project(models.Model):

    name = models.CharField(max_length=200)
