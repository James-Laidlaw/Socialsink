# Generated by Django 4.2.6 on 2023-11-13 05:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_merge_20231030_0157'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Follow',
            new_name='Follower',
        ),
    ]
