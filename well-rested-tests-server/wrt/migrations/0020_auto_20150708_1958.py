# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wrt.attachment


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0019_attachment_detail'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='value',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='attachment',
            name='file',
            field=models.FileField(upload_to=wrt.attachment.upload_to),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('name', 'value')]),
        ),
    ]
