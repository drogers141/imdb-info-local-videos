# Generated by Django 4.1.3 on 2023-06-10 18:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imdb_info_local', '0005_alter_imdbtitlesearchdata_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imdbtitlesearchdata',
            name='rating',
            field=models.FloatField(null=True),
        ),
    ]
