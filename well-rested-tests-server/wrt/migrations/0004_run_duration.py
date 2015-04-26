# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0003_auto_20150426_0644'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='duration',
            field=models.DurationField(null=True, editable=False, blank=True),
        ),
    ]
