from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('creator', models.CharField(max_length=100)),
                ('publication_date', models.DateField()),
                ('_internal_id', models.CharField(blank=True, max_length=50)),
                ('isbn', models.CharField(max_length=20)),
                ('page_count', models.IntegerField()),
                ('is_borrowed', models.BooleanField(default=False)),
                ('borrowed_by', models.CharField(blank=True, max_length=100)),
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('creator', models.CharField(max_length=100)),
                ('publication_date', models.DateField()),
                ('_internal_id', models.CharField(blank=True, max_length=50)),
                ('duration', models.IntegerField()),
                ('format', models.CharField(max_length=10)),
                ('director', models.CharField(blank=True, max_length=100)),
                ('genre', models.CharField(blank=True, max_length=20)),
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='AudioBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('creator', models.CharField(max_length=100)),
                ('publication_date', models.DateField()),
                ('_internal_id', models.CharField(blank=True, max_length=50)),
                ('duration', models.IntegerField()),
                ('narrator', models.CharField(max_length=100)),
                ('is_borrowed', models.BooleanField(default=False)),
                ('borrowed_by', models.CharField(blank=True, max_length=100)),
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='media.movie')),
            ],
            options={
            },
        ),
    ]
