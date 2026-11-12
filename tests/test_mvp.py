from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import CompanyMembership, MembershipRole
from apps.companies.models import Company
from apps.customers.models import Customer
from apps.employees.models import Employee, EmployeeStatus
from apps.finance.models import (
    CashMovement,
    CashMovementKind,
    FinancialCategoryKind,
    FinancialEntry,
    FinancialEntryType,
    FinancialSettlementStatus,
)
from apps.trucks.forms import TruckForm
from apps.trucks.models import Truck, TruckStatus
from apps.trips.models import Trip


User = get_user_model()


class TripFinanceSyncTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Co")
        self.user = User.objects.create_user(username="u1", password="x")
        CompanyMembership.objects.create(
            user=self.user, company=self.company, role=MembershipRole.ADMIN
        )
        self.truck = Truck.objects.create(
            company=self.company, plate="ABC1D23", status=TruckStatus.ACTIVE
        )
        self.driver = Employee.objects.create(
            company=self.company,
            name="Motorista",
            status=EmployeeStatus.ACTIVE,
        )
        self.customer = Customer.objects.create(
            company=self.company,
            name="Cliente X",
        )

    def test_trip_creates_income_entry(self):
        trip = Trip.objects.create(
            company=self.company,
            truck=self.truck,
            driver=self.driver,
            customer=self.customer,
            trip_date="2026-01-15",
            amount_charged=Decimal("500.00"),
        )
        trip.refresh_from_db()
        self.assertIsNotNone(trip.financial_entry_id)
        entry = FinancialEntry.objects.select_related("auto_cash_movement").get(
            pk=trip.financial_entry_id
        )
        self.assertEqual(entry.entry_type, FinancialEntryType.INCOME)
        self.assertEqual(entry.amount, Decimal("500.00"))
        self.assertEqual(entry.category.slug, "trip_income")
        self.assertEqual(entry.category.kind, FinancialCategoryKind.INCOME)
        self.assertEqual(entry.settlement_status, FinancialSettlementStatus.SETTLED)
        self.assertTrue(hasattr(entry, "auto_cash_movement"))
        cm = entry.auto_cash_movement
        self.assertEqual(cm.kind, CashMovementKind.RECEIPT)
        self.assertEqual(cm.amount, Decimal("500.00"))
        self.assertEqual(
            CashMovement.objects.filter(company=self.company, kind=CashMovementKind.RECEIPT).count(),
            1,
        )


class TruckFormTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Frota Test")
        self.user = User.objects.create_user(username="frota", password="x")

    def test_truck_form_create_sets_company_before_validation(self):
        form = TruckForm(
            {
                "plate": "JKL4F56",
                "model": "FH",
                "brand": "Volvo",
                "year": "2019",
                "tank_capacity_liters": "",
                "current_odometer": "",
                "acquisition_date": "",
                "status": TruckStatus.ACTIVE,
                "notes": "",
            },
            company=self.company,
        )
        self.assertTrue(form.is_valid(), form.errors)
        truck = form.save()
        self.assertEqual(truck.company_id, self.company.pk)
        self.assertEqual(Truck.objects.filter(company=self.company, plate="JKL4F56").count(), 1)

    def test_truck_form_accepts_all_empty_except_status(self):
        form = TruckForm(
            {
                "plate": "",
                "model": "",
                "brand": "",
                "year": "",
                "tank_capacity_liters": "",
                "current_odometer": "",
                "acquisition_date": "",
                "status": TruckStatus.ACTIVE,
                "notes": "",
            },
            company=self.company,
        )
        self.assertTrue(form.is_valid(), form.errors)
        truck = form.save()
        self.assertEqual(truck.company_id, self.company.pk)
        self.assertIsNone(truck.plate)
