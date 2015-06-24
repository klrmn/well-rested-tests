import datetime
from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from rest_framework import serializers, viewsets

from result import Result
import permissions


def upload_to(instance, filename):
    return datetime.datetime.now().strftime('%Y%m%d/') + filename


class Attachment(models.Model):
    # this is for the case where the user doesn't want to upload
    # their objects to swift
    file = models.FileField(upload_to=upload_to, null=False, blank=False)

    @property
    def file_url(self):
        return self.file.url

    def __str__(self):
        return self.file_url


class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'file_url')


class AttachmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attachment
        fields = ('id', 'file', 'file_url')


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (permissions.CreateOnly,)


class Detail(models.Model):
    # this will take either Attachment.url or a swift url
    result = models.ForeignKey(Result)
    file_url = models.URLField(null=False, blank=False)
    file_type = models.TextField(null=False, blank=False)
    name = models.TextField(null=False, blank=False)

    def __str__(self):
        return '%s %s' % (self.result.id, self.file_url)


class DetailAdmin(admin.ModelAdmin):
    list_display = ('name', 'file_url', 'file_type', 'result')
    list_filter = ('file_type', 'result')


class DetailSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Detail
        fields = ('id', 'url', 'file_url', 'file_type', 'name', 'result')


class DetailViewSet(viewsets.ModelViewSet):
    queryset = Detail.objects.all()
    serializer_class = DetailSerializer
    permission_classes = (permissions.CreateOnly,)
    filter_fields = ('file_type', 'result', 'name')
