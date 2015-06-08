# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0014_auto_20150518_2157'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='run',
            name='errors',
        ),
        migrations.RemoveField(
            model_name='run',
            name='failures',
        ),
        migrations.RemoveField(
            model_name='run',
            name='tests_run',
        ),
        migrations.RemoveField(
            model_name='run',
            name='xfails',
        ),
        migrations.RemoveField(
            model_name='run',
            name='xpasses',
        ),
    ]
