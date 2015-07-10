# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0020_auto_20150708_1958'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('project', 'name', 'value')]),
        ),
    ]
