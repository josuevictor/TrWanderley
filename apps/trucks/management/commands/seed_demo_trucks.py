"""Semear 2 caminhões fictícios para testes (idempotente por matrícula + empresa)."""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.companies.models import Company
from apps.trucks.models import Truck, TruckStatus


DEMO_TRUCKS = [
    {
        "plate": "DMO-1A23",
        "brand": "Mercedes-Benz",
        "model": "Axor 1933",
        "year": 2018,
        "tank_capacity_liters": Decimal("400"),
        "current_odometer": Decimal("185000.00"),
        "notes": "Veículo de demonstração — testes",
    },
    {
        "plate": "DMO-9Z87",
        "brand": "Volkswagen",
        "model": "Delivery 11.180",
        "year": 2020,
        "tank_capacity_liters": Decimal("350"),
        "current_odometer": Decimal("92000.50"),
        "notes": "Veículo de demonstração — testes",
    },
]


class Command(BaseCommand):
    help = "Cria 2 caminhões de demonstração para a empresa indicada (ou a primeira empresa)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--company-id",
            type=int,
            default=None,
            help="ID da empresa (Company).",
        )
        parser.add_argument(
            "--company-name",
            type=str,
            default=None,
            help="Nome exato da empresa (alternativa ao ID).",
        )

    def handle(self, *args, **options):
        cid = options["company_id"]
        cname = options["company_name"]

        if cid is not None:
            company = Company.objects.filter(pk=cid).first()
            if company is None:
                raise CommandError(f"Empresa com id={cid} não existe.")
        elif cname:
            company = Company.objects.filter(name=cname).first()
            if company is None:
                raise CommandError(f"Empresa com nome «{cname}» não encontrada.")
        else:
            company = Company.objects.order_by("pk").first()
            if company is None:
                raise CommandError(
                    "Nenhuma empresa na base de dados. Crie uma empresa no admin primeiro."
                )
            self.stdout.write(
                self.style.WARNING(
                    f"Usando a primeira empresa: «{company.name}» (id={company.pk}). "
                    "Use --company-id ou --company-name para escolher outra."
                )
            )

        created_count = 0
        for data in DEMO_TRUCKS:
            plate = data["plate"]
            truck, created = Truck.objects.get_or_create(
                company=company,
                plate=plate,
                defaults={
                    "brand": data["brand"],
                    "model": data["model"],
                    "year": data["year"],
                    "tank_capacity_liters": data["tank_capacity_liters"],
                    "current_odometer": data["current_odometer"],
                    "status": TruckStatus.ACTIVE,
                    "notes": data["notes"],
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Criado: {plate} — {truck.brand} {truck.model}"))
            else:
                self.stdout.write(f"Já existia: {plate} — mantido.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído para «{company.name}»: {created_count} novo(s), {len(DEMO_TRUCKS) - created_count} já existente(s)."
            )
        )
