# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0010_auto_20150515_1817'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='project',
            field=models.ForeignKey(default=2, to='wrt.Project'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
