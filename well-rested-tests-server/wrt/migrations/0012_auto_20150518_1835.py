# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0011_auto_20150515_2325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='case',
            field=models.ForeignKey(to='wrt.Case', blank=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='owner',
            field=models.ForeignKey(default=1, blank=True, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='result',
            name='run',
            field=models.ForeignKey(to='wrt.Run', blank=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='start_time',
            field=models.DateTimeField(null=True, verbose_name=b'Start Datetime', blank=True),
        ),
    ]
