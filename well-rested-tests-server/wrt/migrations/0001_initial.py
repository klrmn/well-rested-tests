# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200, verbose_name=b'Test Case Name')),
            ],
        ),
        migrations.CreateModel(
            name='CaseRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField(null=True, verbose_name=b'Start Datetime')),
                ('end_time', models.DateTimeField(auto_now=True, verbose_name=b'End Datetime', null=True)),
                ('duration', models.DurationField(null=True)),
                ('result', models.CharField(default=b'exists', max_length=12, choices=[(b'exists', b'exists'), (b'pass', b'pass'), (b'fail', b'fail'), (b'skip', b'skip'), (b'unknown', b'unknown'), (b'inprogress', b'inprogress')])),
                ('reason', models.TextField(null=True)),
                ('case', models.ForeignKey(to='wrt.Case')),
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
                ('end_time', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(to='wrt.Project')),
            ],
        ),
        migrations.CreateModel(
            name='RunEnvVar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name=b'Environmental Variable')),
                ('value', models.CharField(max_length=200)),
                ('run', models.ForeignKey(to='wrt.Run')),
            ],
        ),
        migrations.CreateModel(
            name='ImageAttachment',
            fields=[
                ('attachment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wrt.Attachment')),
                ('file', models.ImageField(upload_to=b'screenshots', editable=False)),
            ],
            bases=('wrt.attachment',),
        ),
        migrations.CreateModel(
            name='TextAttachment',
            fields=[
                ('attachment_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='wrt.Attachment')),
                ('file', models.FileField(upload_to=b'text', editable=False)),
            ],
            bases=('wrt.attachment',),
        ),
        migrations.AddField(
            model_name='caserun',
            name='run',
            field=models.ForeignKey(to='wrt.Run'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='case_run',
            field=models.ForeignKey(to='wrt.CaseRun'),
        ),
    ]
