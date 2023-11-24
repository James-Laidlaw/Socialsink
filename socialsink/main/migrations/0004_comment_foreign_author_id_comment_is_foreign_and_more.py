# Generated by Django 4.2.6 on 2023-11-24 09:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_remove_post_edited'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='foreign_author_id',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='is_foreign',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='follower',
            name='foreign_follower_id',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='follower',
            name='is_foreign',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='like',
            name='context',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='like',
            name='foreign_author_id',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='like',
            name='is_foreign',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='main.author'),
        ),
        migrations.AlterField(
            model_name='follower',
            name='follower',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='following', to='main.author'),
        ),
        migrations.AlterField(
            model_name='like',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='main.author'),
        ),
        migrations.CreateModel(
            name='Inbox',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inbox', to='main.author')),
            ],
        ),
    ]
