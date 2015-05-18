# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0013_auto_20150518_1840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='status',
            field=models.CharField(default=b'exists', max_length=12, null=True, blank=True, choices=[(b'exists', b'exists'), (b'pass', b'pass'), (b'xpass', b'xpass'), (b'xfail', b'xfail'), (b'fail', b'fail'), (b'skip', b'skip'), (b'unknown', b'unknown'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')]),
        ),
    ]
