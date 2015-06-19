# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wrt.attachment


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0018_auto_20150619_0336'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to=wrt.attachment.upload_to, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='Detail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_url', models.URLField()),
                ('file_type', models.TextField()),
                ('name', models.TextField()),
                ('result', models.ForeignKey(to='wrt.Result')),
            ],
        ),
    ]
