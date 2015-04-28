from django.db import models         # models.py
from django.shortcuts import render  # views.py
from django.contrib import admin     # admin.py
from django.test import TestCase     # tests.py
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets

import permissions


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    # TODO: figure out how to make it so you can only see your own user
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AuthenticatedReadOnly,)
