# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0005_auto_20150426_0659'),
    ]

    operations = [
        migrations.AlterField(
            model_name='caserun',
            name='result',
            field=models.CharField(default=b'exists', max_length=12, null=True, blank=True, choices=[(b'exists', b'exists'), (b'pass', b'pass'), (b'fail', b'fail'), (b'skip', b'skip'), (b'unknown', b'unknown'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')]),
        ),
    ]
