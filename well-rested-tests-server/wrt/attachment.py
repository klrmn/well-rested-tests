from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

from result import Result
import permissions


class Attachment(models.Model):
    result = models.ForeignKey(Result)


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
        fields = ('id', 'url', 'result', 'file')


class TextSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TextAttachment
        fields = ('id', 'url', 'result', 'file')


# ViewSets define the view behavior.
class ImageViewSet(viewsets.ModelViewSet):
    queryset = ImageAttachment.objects.all()
    serializer_class = ImageSerializer
    permission_classes = (permissions.CreateOnly,)


class TextViewSet(viewsets.ModelViewSet):
    queryset = TextAttachment.objects.all()
    serializer_class = TextSerializer
    permission_classes = (permissions.CreateOnly,)
