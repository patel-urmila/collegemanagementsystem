# Generated by Django 4.2 on 2023-05-02 09:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "studentManagementApp",
            "0005_alter_subjects_teacher_alter_teachers_user_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentLeave",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("leaveDate", models.DateField()),
                ("reason", models.CharField(max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Reject", "Reject"),
                            ("Approve", "Approve"),
                            ("Requested", "Requested"),
                        ],
                        max_length=254,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="studentManagementApp.students",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StaffLeave",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("leaveDate", models.DateField()),
                ("reason", models.CharField(max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Reject", "Reject"),
                            ("Approve", "Approve"),
                            ("Requested", "Requested"),
                        ],
                        max_length=254,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="studentManagementApp.teachers",
                    ),
                ),
            ],
        ),
    ]
