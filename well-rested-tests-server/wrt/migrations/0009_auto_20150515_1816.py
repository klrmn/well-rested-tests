# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0008_auto_20150514_2337'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='erros',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='failures',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='status',
            field=models.CharField(blank=True, max_length=12, null=True, choices=[(b'pass', b'pass'), (b'fail', b'fail'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')]),
        ),
        migrations.AddField(
            model_name='run',
            name='tests_run',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='xfails',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='xpasses',
            field=models.IntegerField(default=0, blank=True),
        ),
    ]
