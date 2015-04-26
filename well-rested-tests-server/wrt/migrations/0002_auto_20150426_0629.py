# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wrt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='user',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='end_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='run',
            name='project',
            field=models.ForeignKey(editable=False, to='wrt.Project'),
        ),
    ]
