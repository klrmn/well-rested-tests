# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0017_case_fixture'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attachment',
            name='result',
        ),
        migrations.RemoveField(
            model_name='imageattachment',
            name='attachment_ptr',
        ),
        migrations.RemoveField(
            model_name='textattachment',
            name='attachment_ptr',
        ),
        migrations.DeleteModel(
            name='Attachment',
        ),
        migrations.DeleteModel(
            name='ImageAttachment',
        ),
        migrations.DeleteModel(
            name='TextAttachment',
        ),
    ]
