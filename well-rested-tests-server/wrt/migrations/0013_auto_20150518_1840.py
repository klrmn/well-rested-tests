# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('wrt', '0012_auto_20150518_1835'),
    ]

    operations = [
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
            name='run',
            field=models.ForeignKey(to='wrt.Run'),
        ),
    ]
