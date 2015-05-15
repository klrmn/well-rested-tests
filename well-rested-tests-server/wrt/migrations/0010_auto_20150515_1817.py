# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0009_auto_20150515_1816'),
    ]

    operations = [
        migrations.RenameField(
            model_name='run',
            old_name='erros',
            new_name='errors',
        ),
    ]
