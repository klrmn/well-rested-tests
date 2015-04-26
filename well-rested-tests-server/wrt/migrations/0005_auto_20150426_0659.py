# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0004_run_duration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caserun',
            name='duration',
            field=models.DurationField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='caserun',
            name='end_time',
            field=models.DateTimeField(null=True, verbose_name=b'End Datetime', blank=True),
        ),
        migrations.AlterField(
            model_name='caserun',
            name='reason',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='caserun',
            name='result',
            field=models.CharField(default=b'exists', max_length=12, blank=True, choices=[(b'exists', b'exists'), (b'pass', b'pass'), (b'fail', b'fail'), (b'skip', b'skip'), (b'unknown', b'unknown'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')]),
        ),
    ]
