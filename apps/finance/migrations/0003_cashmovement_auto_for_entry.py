import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0002_mvp"),
    ]

    operations = [
        migrations.AddField(
            model_name="cashmovement",
            name="auto_for_entry",
            field=models.OneToOneField(
                blank=True,
                help_text="Preenchido no modo caderno: um movimento por lançamento.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="auto_cash_movement",
                to="finance.financialentry",
                verbose_name="Lançamento (caixa automático)",
            ),
        ),
    ]
