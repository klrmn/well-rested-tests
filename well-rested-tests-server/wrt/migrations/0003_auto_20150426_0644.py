# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0002_auto_20150426_0629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='project',
            field=models.ForeignKey(to='wrt.Project'),
        ),
        migrations.AlterField(
            model_name='run',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
