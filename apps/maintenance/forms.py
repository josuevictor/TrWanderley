from decimal import Decimal

from django import forms
from django.db.models import Q

from apps.core.money import format_br_decimal, parse_br_decimal
from apps.finance.forms import T_INPUT, T_SELECT
from apps.suppliers.models import Supplier
from apps.trucks.models import Truck, TruckStatus

from .models import MaintenanceRecord

MONEY_INPUT_CLASS = (
    T_INPUT + " money-br placeholder:text-slate-400"
)  # máscara via JS no template
MONEY_HELP = "Use formato brasileiro: 1.234,56 (milhar com ponto, centavos com vírgula)."


class MaintenanceForm(forms.ModelForm):
    """Campos monetários como texto para aceitar vírgula (BR); parse em clean_*."""

    class Meta:
        model = MaintenanceRecord
        fields = [
            "truck",
            "kind",
            "title",
            "description",
            "workshop",
            "workshop_name",
            "service_date",
            "odometer_km",
            "parts_amount",
            "labor_amount",
            "total_amount",
            "next_service_date",
            "next_service_odometer",
            "receipt",
            "notes",
        ]
        widgets = {
            "truck": forms.Select(attrs={"class": T_SELECT}),
            "kind": forms.Select(attrs={"class": T_SELECT}),
            "title": forms.TextInput(attrs={"class": T_INPUT}),
            "description": forms.Textarea(attrs={"class": T_INPUT + " min-h-[64px]", "rows": 2}),
            "workshop": forms.Select(attrs={"class": T_SELECT}),
            "workshop_name": forms.TextInput(attrs={"class": T_INPUT}),
            "service_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "receipt": forms.FileInput(attrs={"class": T_INPUT}),
            "notes": forms.Textarea(attrs={"class": T_INPUT + " min-h-[64px]", "rows": 2}),
        }

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        tq = Q(company=company, status__in=[TruckStatus.ACTIVE, TruckStatus.MAINTENANCE])
        if self.instance.pk and self.instance.truck_id:
            tq |= Q(pk=self.instance.truck_id)
        self.fields["truck"].queryset = Truck.objects.filter(tq).distinct().order_by("plate")
        wq = Q(company=company)
        if self.instance.pk and self.instance.workshop_id:
            wq |= Q(pk=self.instance.workshop_id)
        self.fields["workshop"].queryset = Supplier.objects.filter(wq).distinct().order_by("name")
        self.fields["workshop"].required = False

        # Campos km opcionais
        for fname, label, required, help_txt, ph in [
            ("odometer_km", "Quilometragem", False, "Opcional.", "0,00"),
            ("next_service_odometer", "Próxima manutenção (km)", False, "Opcional.", "0,00"),
        ]:
            initial = ""
            if self.instance.pk and fname in ("odometer_km", "next_service_odometer"):
                val = getattr(self.instance, fname, None)
                if val is not None:
                    initial = format_br_decimal(val)

            self.fields[fname] = forms.CharField(
                label=label,
                required=required,
                help_text=help_txt,
                initial=initial,
                widget=forms.TextInput(
                    attrs={
                        "class": MONEY_INPUT_CLASS,
                        "placeholder": ph,
                        "inputmode": "decimal",
                        "autocomplete": "off",
                    }
                ),
            )

        parts_init = ""
        labor_init = ""
        total_init = ""
        if self.instance.pk:
            if self.instance.parts_amount is not None:
                parts_init = format_br_decimal(self.instance.parts_amount)
            if self.instance.labor_amount is not None:
                labor_init = format_br_decimal(self.instance.labor_amount)
            if self.instance.total_amount is not None:
                total_init = format_br_decimal(self.instance.total_amount)

        self.fields["parts_amount"] = forms.CharField(
            label="Valor peças",
            required=False,
            help_text=MONEY_HELP,
            initial=parts_init,
            widget=forms.TextInput(
                attrs={
                    "class": MONEY_INPUT_CLASS,
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )
        self.fields["labor_amount"] = forms.CharField(
            label="Mão de obra",
            required=False,
            help_text=MONEY_HELP,
            initial=labor_init,
            widget=forms.TextInput(
                attrs={
                    "class": MONEY_INPUT_CLASS,
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )
        self.fields["total_amount"] = forms.CharField(
            label="Valor total",
            required=False,
            help_text="Calculado automaticamente: valor peças + mão de obra.",
            initial=total_init,
            widget=forms.TextInput(
                attrs={
                    "class": MONEY_INPUT_CLASS
                    + " bg-slate-50 dark:bg-slate-800/80 maintenance-total-readonly",
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "readonly": True,
                    "tabindex": "-1",
                    "aria-readonly": "true",
                    "autocomplete": "off",
                }
            ),
        )

    def _parse_money(self, field_name, *, allow_empty_as_zero=False):
        raw = self.cleaned_data.get(field_name, "")
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            if allow_empty_as_zero:
                return Decimal("0")
            return None
        try:
            return parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e

    def clean_parts_amount(self):
        v = self._parse_money("parts_amount", allow_empty_as_zero=True)
        if v is not None and v < 0:
            raise forms.ValidationError("O valor não pode ser negativo.")
        return v if v is not None else Decimal("0")

    def clean_labor_amount(self):
        v = self._parse_money("labor_amount", allow_empty_as_zero=True)
        if v is not None and v < 0:
            raise forms.ValidationError("O valor não pode ser negativo.")
        return v if v is not None else Decimal("0")

    def clean_odometer_km(self):
        v = self._parse_money("odometer_km", allow_empty_as_zero=False)
        if v is None:
            return None
        if v < 0:
            raise forms.ValidationError("Quilometragem inválida.")
        return v

    def clean_next_service_odometer(self):
        v = self._parse_money("next_service_odometer", allow_empty_as_zero=False)
        if v is None:
            return None
        if v < 0:
            raise forms.ValidationError("Valor inválido.")
        return v

    def clean(self):
        data = super().clean()
        parts = data.get("parts_amount")
        labor = data.get("labor_amount")
        if parts is None or labor is None:
            return data
        data["total_amount"] = parts + labor
        if data["total_amount"] <= 0:
            raise forms.ValidationError(
                {"total_amount": "O valor total (peças + mão de obra) deve ser maior que zero."}
            )
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        obj.parts_amount = self.cleaned_data["parts_amount"]
        obj.labor_amount = self.cleaned_data["labor_amount"]
        obj.total_amount = self.cleaned_data["total_amount"]
        obj.odometer_km = self.cleaned_data.get("odometer_km")
        obj.next_service_odometer = self.cleaned_data.get("next_service_odometer")
        if commit:
            obj.full_clean()
            obj.save()
        return obj
