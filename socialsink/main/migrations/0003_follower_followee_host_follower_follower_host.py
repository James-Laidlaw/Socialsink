# Generated by Django 4.2.7 on 2023-11-26 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_remove_author_follows_remove_author_friends_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="follower",
            name="followee_host",
            field=models.CharField(default="", max_length=1000),
        ),
        migrations.AddField(
            model_name="follower",
            name="follower_host",
            field=models.CharField(default="", max_length=1000),
        ),
    ]
