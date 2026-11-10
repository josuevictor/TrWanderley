# Generated manually for CustomerDeliveryPlace

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerDeliveryPlace",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("label", models.CharField(blank=True, max_length=120, verbose_name="Nome do local (opcional)")),
                ("address_line", models.CharField(max_length=512, verbose_name="Endereço / local de entrega")),
                ("sort_order", models.PositiveSmallIntegerField(default=0, verbose_name="Ordem")),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delivery_places",
                        to="customers.customer",
                        verbose_name="Cliente",
                    ),
                ),
            ],
            options={
                "verbose_name": "Local de entrega",
                "verbose_name_plural": "Locais de entrega",
                "ordering": ["sort_order", "pk"],
            },
        ),
        migrations.AddIndex(
            model_name="customerdeliveryplace",
            index=models.Index(fields=["customer", "sort_order"], name="customers_cd_customer_sort_idx"),
        ),
    ]
