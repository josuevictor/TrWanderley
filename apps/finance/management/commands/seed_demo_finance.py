"""Semear contas, lançamentos e movimentos de caixa de treino (3 de cada, idempotente)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.companies.models import Company
from apps.finance.models import (
    CashMovement,
    CashMovementKind,
    FinancialAccount,
    FinancialAccountKind,
    FinancialCategory,
    FinancialCategoryKind,
    FinancialEntry,
    FinancialEntryType,
    PaymentMethod,
)
from apps.finance.services import ensure_default_categories, sync_auto_cash_for_entry

DEMO_ACCOUNT_MARKER = "Demo · "

DEMO_ACCOUNTS: list[tuple[str, str]] = [
    ("Demo · Caixa matriz", FinancialAccountKind.CASH),
    ("Demo · Conta Nubank", FinancialAccountKind.DIGITAL),
    ("Demo · Banco Bradesco", FinancialAccountKind.BANK),
]

DEMO_ENTRY_DESCRIPTIONS: list[str] = [
    "[Treino] Material de escritório — compra mensal",
    "[Treino] Aluguel galpão — novembro",
    "[Treino] Venda serviço extra — à vista",
]

DEMO_CASH_MEMOS: list[str] = [
    "[Treino] Recebimento avulso PIX (sem lançamento)",
]


def _resolve_company(options) -> Company:
    cid = options["company_id"]
    cname = options["company_name"]
    if cid is not None:
        company = Company.objects.filter(pk=cid).first()
        if company is None:
            raise CommandError(f"Empresa com id={cid} não existe.")
        return company
    if cname:
        company = Company.objects.filter(name=cname).first()
        if company is None:
            raise CommandError(f"Empresa com nome «{cname}» não encontrada.")
        return company
    company = Company.objects.order_by("pk").first()
    if company is None:
        raise CommandError(
            "Nenhuma empresa na base de dados. Crie uma empresa no admin primeiro."
        )
    return company


def _payment_method(company: Company, preferred: tuple[str, ...]) -> PaymentMethod | None:
    for name in preferred:
        pm = PaymentMethod.objects.filter(company=company, name__iexact=name).first()
        if pm:
            return pm
    return PaymentMethod.objects.filter(company=company, is_active=True).first()


class Command(BaseCommand):
    help = (
        "Cria 3 contas, 3 lançamentos e 3 movimentos de caixa de exemplo "
        "(marcados [Treino] / Demo ·), idempotente por nome/descrição."
    )

    def add_arguments(self, parser):
        parser.add_argument("--company-id", type=int, default=None)
        parser.add_argument("--company-name", type=str, default=None)

    @transaction.atomic
    def handle(self, *args, **options):
        company = _resolve_company(options)
        if not options["company_id"] and not options["company_name"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Usando a primeira empresa: «{company.name}» (id={company.pk})."
                )
            )

        ensure_default_categories(company)
        today = timezone.localdate()
        pm_pix = _payment_method(company, ("Pix", "PIX"))
        pm_cash = _payment_method(company, ("Dinheiro", "Dinheiro físico"))

        cat_income = FinancialCategory.objects.get(
            company=company, kind=FinancialCategoryKind.INCOME, slug="other_income"
        )
        cat_expense = FinancialCategory.objects.get(
            company=company, kind=FinancialCategoryKind.EXPENSE, slug="other_expense"
        )

        accounts: dict[str, FinancialAccount] = {}
        for name, kind in DEMO_ACCOUNTS:
            acc, created = FinancialAccount.objects.get_or_create(
                company=company,
                name=name,
                defaults={"kind": kind, "is_active": True},
            )
            accounts[name] = acc
            self._log_row("Conta", name, created)

        acc_matriz = accounts["Demo · Caixa matriz"]
        acc_nubank = accounts["Demo · Conta Nubank"]

        entry_specs = [
            {
                "description": DEMO_ENTRY_DESCRIPTIONS[0],
                "entry_type": FinancialEntryType.EXPENSE,
                "category": cat_expense,
                "amount": Decimal("1800.00"),
                "competence_date": today - timedelta(days=5),
                "due_date": today + timedelta(days=10),
                "default_account": acc_matriz,
                "payment_method": pm_pix,
            },
            {
                "description": DEMO_ENTRY_DESCRIPTIONS[1],
                "entry_type": FinancialEntryType.EXPENSE,
                "category": cat_expense,
                "amount": Decimal("2500.00"),
                "competence_date": today - timedelta(days=2),
                "due_date": today + timedelta(days=5),
                "default_account": acc_nubank,
                "payment_method": pm_pix,
            },
            {
                "description": DEMO_ENTRY_DESCRIPTIONS[2],
                "entry_type": FinancialEntryType.INCOME,
                "category": cat_income,
                "amount": Decimal("950.00"),
                "competence_date": today,
                "due_date": None,
                "default_account": acc_nubank,
                "payment_method": pm_pix,
            },
        ]
        entries: dict[str, FinancialEntry] = {}
        for spec in entry_specs:
            entry, created = FinancialEntry.objects.get_or_create(
                company=company,
                description=spec["description"],
                defaults={
                    "entry_type": spec["entry_type"],
                    "category": spec["category"],
                    "amount": spec["amount"],
                    "competence_date": spec["competence_date"],
                    "due_date": spec["due_date"],
                    "default_account": spec["default_account"],
                    "payment_method": spec["payment_method"],
                    "is_system_generated": False,
                    "notes": "Dados de treino — seed_demo_finance.",
                },
            )
            entries[spec["description"]] = entry
            sync_auto_cash_for_entry(entry)
            self._log_row("Lançamento", spec["description"], created)

        cm, cm_created = CashMovement.objects.get_or_create(
            company=company,
            memo=DEMO_CASH_MEMOS[0],
            defaults={
                "financial_account": acc_matriz,
                "kind": CashMovementKind.RECEIPT,
                "amount": Decimal("350.00"),
                "movement_date": today - timedelta(days=1),
                "payment_method": pm_pix,
            },
        )
        self._log_row("Caixa avulso", DEMO_CASH_MEMOS[0], cm_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído para «{company.name}»: 3 contas, 3 lançamentos "
                f"(caixa automático por lançamento) + 1 movimento avulso de exemplo."
            )
        )

    def _log_row(self, label: str, name: str, created: bool) -> None:
        if created:
            self.stdout.write(self.style.SUCCESS(f"{label} criado: {name}"))
        else:
            self.stdout.write(f"{label} já existia: {name}")
