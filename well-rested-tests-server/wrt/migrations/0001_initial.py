# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import wrt.attachment


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200, verbose_name=b'Test Case Name')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('project', models.ForeignKey(to='wrt.Project')),
                ('duration', models.DurationField(null=True, editable=False, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField(null=True, verbose_name=b'Start Datetime')),
                ('end_time', models.DateTimeField(null=True, verbose_name=b'End Datetime', blank=True)),
                ('duration', models.DurationField(null=True, blank=True)),
                ('status', models.CharField(default=b'exists', max_length=12, null=True, blank=True, choices=[(b'exists', b'exists'), (b'pass', b'pass'), (b'fail', b'fail'), (b'skip', b'skip'), (b'unknown', b'unknown'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')])),
                ('reason', models.TextField(null=True, blank=True)),
                ('case', models.ForeignKey(to='wrt.Case')),
                ('owner', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='run',
            name='owner',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='run',
            field=models.ForeignKey(to='wrt.Run'),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('project', models.ForeignKey(to='wrt.Project')),
                ('value', models.CharField(default='', max_length=200)),
            ],
        ),
        migrations.AlterField(
            model_name='run',
            name='start_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='tags',
            field=models.ManyToManyField(to=b'wrt.Tag', blank=True),
        ),
        migrations.AddField(
            model_name='run',
            name='status',
            field=models.CharField(blank=True, max_length=12, null=True, choices=[(b'pass', b'pass'), (b'fail', b'fail'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')]),
        ),
        migrations.AddField(
            model_name='case',
            name='project',
            field=models.ForeignKey(default=2, to='wrt.Project'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='result',
            name='case',
            field=models.ForeignKey(to='wrt.Case', blank=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='owner',
            field=models.ForeignKey(default=1, blank=True, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='result',
            name='start_time',
            field=models.DateTimeField(null=True, verbose_name=b'Start Datetime', blank=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='case',
            field=models.ForeignKey(to='wrt.Case'),
        ),
        migrations.AlterField(
            model_name='result',
            name='owner',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='result',
            name='status',
            field=models.CharField(default=b'exists', max_length=12, null=True, blank=True, choices=[(b'exists', b'exists'), (b'pass', b'pass'), (b'xpass', b'xpass'), (b'xfail', b'xfail'), (b'fail', b'fail'), (b'skip', b'skip'), (b'unknown', b'unknown'), (b'inprogress', b'inprogress'), (b'aborted', b'aborted')]),
        ),
        migrations.RemoveField(
            model_name='run',
            name='duration',
        ),
        migrations.AddField(
            model_name='case',
            name='fixture',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(upload_to=wrt.attachment.upload_to)),
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
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('name', 'value')]),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('project', 'name', 'value')]),
        ),
    ]
