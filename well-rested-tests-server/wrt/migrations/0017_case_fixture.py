# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0016_remove_run_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='fixture',
            field=models.BooleanField(default=False),
        ),
    ]
