# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wrt', '0006_auto_20150426_0700'),
    ]

    operations = [
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
        migrations.RemoveField(
            model_name='caserun',
            name='case',
        ),
        migrations.RemoveField(
            model_name='caserun',
            name='run',
        ),
        migrations.RemoveField(
            model_name='attachment',
            name='case_run',
        ),
        migrations.RemoveField(
            model_name='run',
            name='user',
        ),
        migrations.AddField(
            model_name='run',
            name='owner',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.DeleteModel(
            name='CaseRun',
        ),
        migrations.AddField(
            model_name='result',
            name='run',
            field=models.ForeignKey(to='wrt.Run'),
        ),
        migrations.AddField(
            model_name='attachment',
            name='result',
            field=models.ForeignKey(default=1, to='wrt.Result'),
            preserve_default=False,
        ),
    ]
