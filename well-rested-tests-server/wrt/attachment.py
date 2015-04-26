from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

from case_run import CaseRun


class Attachment(models.Model):
    case_run = models.ForeignKey(CaseRun)


class ImageAttachment(Attachment):
    file = models.ImageField(upload_to='screenshots',
                             null=False, editable=False)


class TextAttachment(Attachment):
    file = models.FileField(upload_to='text',
                            null=False, editable=False)


# Serializers define the API representation.
class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ImageAttachment
        fields = ('id', 'url', 'case_run', 'file')


class TextSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TextAttachment
        fields = ('id', 'url', 'case_run', 'file')


# ViewSets define the view behavior.
class ImageViewSet(viewsets.ModelViewSet):
    queryset = ImageAttachment.objects.all()
    serializer_class = ImageSerializer


class TextViewSet(viewsets.ModelViewSet):
    queryset = TextAttachment.objects.all()
    serializer_class = TextSerializer
