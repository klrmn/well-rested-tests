from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

from result import Result
import permissions


def upload_to(instance, filename):
    file_type = filename.split('.')[-1]
    return '%s/%%Y/%%m/%%d/%%H_%%M_%%S-%s' % (file_type, filename)


class Attachment(models.Model):
    # this is for the case where the user doesn't want to upload
    # their objects to swift
    file = models.FileField(upload_to=upload_to,
                            null=False, editable=False)
    @property
    def file_url(self):
        return self.file.url


class Detail(models.Model):
    # this will take either Attachment.url or a swift url
    result = models.ForeignKey(Result)
    file_url = models.URLField(null=False, blank=False)
    file_type = models.TextField(null=False, blank=False)
    name = models.TextField(null=False, blank=False)


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')


class DetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'result', 'file_url', 'file_type')
    list_filter = ('result', 'file_type')


# Serializers define the API representation.
class AttachmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attachment
        fields = ('id', 'url', 'file', 'file_url')


class DetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Detail
        fields = ('id', 'url', 'file_url', 'file_type', 'name')


# ViewSets define the view behavior.
class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (permissions.CreateOnly,)


class DetailViewSet(viewsets.ModelViewSet):
    queryset = Detail.objects.all()
    serializer_class = DetailSerializer
    permission_classes = (permissions.CreateOnly,)
