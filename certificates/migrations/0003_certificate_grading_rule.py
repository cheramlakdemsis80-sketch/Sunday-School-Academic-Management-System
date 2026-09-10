from django.db import migrations, models


DEFAULT_GRADING_RULE = """100 – 90  →  በጣም ጥሩ
89 – 80   →  ጥሩ
79 – 60   → መካከለኛ
59 – 50   → ደካማ / አልፏል
ከ 50 በታች → አላለፈም"""


class Migration(migrations.Migration):
    dependencies = [
        ("certificates", "0002_certificate_admin_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="certificate",
            name="grading_rule",
            field=models.TextField(blank=True, default=DEFAULT_GRADING_RULE),
        ),
    ]
