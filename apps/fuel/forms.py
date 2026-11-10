from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.db.models import Q

from apps.core.money import format_br_decimal, parse_br_decimal
from apps.employees.models import Employee, EmployeeStatus
from apps.finance.models import PaymentMethod
from apps.suppliers.models import Supplier
from apps.trucks.models import Truck, TruckStatus

from .models import FuelEntry

# Mais compacto no telemóvel (max-w-full evita overflow horizontal).
FUEL_INPUT = (
    "fuel-field block w-full max-w-full min-w-0 box-border rounded-lg border border-slate-200 "
    "bg-white px-2.5 py-1.5 text-base leading-snug md:text-sm min-h-[2.375rem] "
    "text-slate-900 "
    "focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 "
    "dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
)
FUEL_SELECT = FUEL_INPUT + " truncate"
FUEL_FILE = (
    FUEL_INPUT
    + " text-sm file:mr-2 file:max-w-[45%] file:truncate file:rounded-md file:border-0 "
    "file:bg-slate-100 file:px-2 file:py-1 file:text-xs file:font-medium "
    "dark:file:bg-slate-700 dark:file:text-slate-100"
)

MONEY_INPUT_CLASS = FUEL_INPUT + " money-br placeholder:text-slate-400"
LITERS_INPUT_CLASS = FUEL_INPUT + " dec-br-3 placeholder:text-slate-400"
PRICE_INPUT_CLASS = FUEL_INPUT + " dec-br-4 placeholder:text-slate-400"
MONEY_HELP = "Use formato brasileiro: 1.234,56 (milhar com ponto, centavos com vírgula)."


class FuelEntryForm(forms.ModelForm):
    """Decimais como texto (vírgula BR); total preenchido no cliente e validado no servidor."""

    class Meta:
        model = FuelEntry
        fields = [
            "fuel_date",
            "truck",
            "driver",
            "supplier",
            "station_name",
            "fuel_type",
            "liters",
            "price_per_liter",
            "total_amount",
            "odometer_km",
            "payment_method",
            "receipt",
        ]
        widgets = {
            "fuel_date": forms.DateInput(
                attrs={"type": "date", "class": FUEL_INPUT, "autocomplete": "off"}
            ),
            "truck": forms.Select(attrs={"class": FUEL_SELECT}),
            "driver": forms.Select(attrs={"class": FUEL_SELECT}),
            "supplier": forms.Select(attrs={"class": FUEL_SELECT}),
            "station_name": forms.TextInput(attrs={"class": FUEL_INPUT}),
            "fuel_type": forms.Select(attrs={"class": FUEL_SELECT}),
            "payment_method": forms.Select(attrs={"class": FUEL_SELECT}),
            "receipt": forms.ClearableFileInput(attrs={"class": FUEL_FILE}),
        }

    def __init__(self, *args, company, driver_employee=None, **kwargs):
        self.company = company
        self.driver_employee = driver_employee
        super().__init__(*args, **kwargs)

        tq = Q(company=company, status=TruckStatus.ACTIVE)
        if self.instance.pk and self.instance.truck_id:
            tq |= Q(pk=self.instance.truck_id)
        self.fields["truck"].queryset = Truck.objects.filter(tq).distinct().order_by("plate")
        dq = Q(company=company, status=EmployeeStatus.ACTIVE)
        if self.instance.pk and self.instance.driver_id:
            dq |= Q(pk=self.instance.driver_id)
        self.fields["driver"].queryset = Employee.objects.filter(dq).distinct().order_by("name")
        sq = Q(company=company)
        if self.instance.pk and self.instance.supplier_id:
            sq |= Q(pk=self.instance.supplier_id)
        self.fields["supplier"].queryset = Supplier.objects.filter(sq).distinct().order_by("name")
        self.fields["supplier"].required = False
        pq = Q(company=company, is_active=True)
        if self.instance.pk and self.instance.payment_method_id:
            pq |= Q(pk=self.instance.payment_method_id)
        self.fields["payment_method"].queryset = PaymentMethod.objects.filter(pq).distinct().order_by(
            "name"
        )
        self.fields["payment_method"].required = False

        if driver_employee is not None:
            del self.fields["driver"]
            if driver_employee.truck_id:
                self.fields["truck"].queryset = Truck.objects.filter(
                    pk=driver_employee.truck_id,
                    company=company,
                )

        specs = [
            (
                "liters",
                "Litros",
                True,
                "Quantidade abastecida (ex.: 50 ou 50,125).",
                "0,000",
                3,
                LITERS_INPUT_CLASS,
            ),
            (
                "price_per_liter",
                "Preço por litro",
                True,
                MONEY_HELP,
                "0,0000",
                4,
                PRICE_INPUT_CLASS,
            ),
            (
                "total_amount",
                "Valor total",
                False,
                "Preenchido automaticamente: litros × preço por litro.",
                "0,00",
                2,
                MONEY_INPUT_CLASS + " bg-slate-50 dark:bg-slate-800/80",
            ),
            (
                "odometer_km",
                "Quilometragem",
                False,
                "Opcional. " + MONEY_HELP,
                "0,00",
                2,
                MONEY_INPUT_CLASS,
            ),
        ]

        for fname, label, required, help_txt, ph, places, css in specs:
            initial = ""
            if self.instance.pk and getattr(self.instance, fname, None) is not None:
                initial = format_br_decimal(getattr(self.instance, fname), places=places)

            extra_attrs = {
                "class": css,
                "placeholder": ph,
                "inputmode": "decimal",
                "autocomplete": "off",
            }
            if fname == "total_amount":
                extra_attrs["class"] = css + " fuel-total-readonly"
                extra_attrs["readonly"] = True
                extra_attrs["tabindex"] = "-1"
                extra_attrs["aria-readonly"] = "true"

            self.fields[fname] = forms.CharField(
                label=label,
                required=required,
                help_text=help_txt,
                initial=initial,
                widget=forms.TextInput(attrs=extra_attrs),
            )

    def _parse_decimal(self, field_name: str, label: str, *, required: bool) -> Decimal | None:
        raw = self.cleaned_data.get(field_name, "")
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if required:
                raise forms.ValidationError(f"Indique {label}.")
            return None
        try:
            return parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e

    def clean_liters(self):
        v = self._parse_decimal("liters", "os litros", required=True)
        assert v is not None
        if v <= 0:
            raise forms.ValidationError("Litros devem ser positivos.")
        return v

    def clean_price_per_liter(self):
        v = self._parse_decimal("price_per_liter", "o preço por litro", required=True)
        assert v is not None
        if v < 0:
            raise forms.ValidationError("Preço por litro inválido.")
        return v

    def clean_odometer_km(self):
        v = self._parse_decimal("odometer_km", "a quilometragem", required=False)
        if v is None:
            return None
        if v < 0:
            raise forms.ValidationError("Quilometragem inválida.")
        return v

    def clean(self):
        data = super().clean()
        liters = data.get("liters")
        price = data.get("price_per_liter")
        if liters is None or price is None:
            return data
        calc = (liters * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        data["total_amount"] = calc
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        if self.driver_employee is not None:
            obj.driver = self.driver_employee
        obj.liters = self.cleaned_data["liters"]
        obj.price_per_liter = self.cleaned_data["price_per_liter"]
        obj.total_amount = self.cleaned_data["total_amount"]
        obj.odometer_km = self.cleaned_data.get("odometer_km")
        if commit:
            obj.full_clean()
            obj.save()
        return obj
