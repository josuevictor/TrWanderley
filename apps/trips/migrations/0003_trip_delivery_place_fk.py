# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0002_customerdeliveryplace"),
        ("trips", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="trip",
            name="delivery_place_ref",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="trips",
                to="customers.customerdeliveryplace",
                verbose_name="Local de entrega (cadastro)",
            ),
        ),
    ]
