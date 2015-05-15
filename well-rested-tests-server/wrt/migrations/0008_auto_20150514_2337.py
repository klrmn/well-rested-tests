# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0007_auto_20150428_1610'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('project', models.ForeignKey(to='wrt.Project')),
            ],
        ),
        migrations.RemoveField(
            model_name='runenvvar',
            name='run',
        ),
        migrations.AlterField(
            model_name='run',
            name='start_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.DeleteModel(
            name='RunEnvVar',
        ),
        migrations.AddField(
            model_name='run',
            name='tags',
            field=models.ManyToManyField(to='wrt.Tag', blank=True),
        ),
    ]
