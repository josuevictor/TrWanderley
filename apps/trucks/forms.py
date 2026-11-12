from decimal import Decimal

from django import forms

from apps.core.form_utils import finalize_company_form
from apps.core.money import format_br_decimal, parse_br_decimal
from apps.finance.forms import T_INPUT, T_SELECT

from .models import Truck, TruckStatus

MONEY_INPUT_CLASS = T_INPUT + " money-br placeholder:text-slate-400"


class TruckForm(forms.ModelForm):
    """Decimais como texto (BR); ano inteiro sem separadores milhar."""

    class Meta:
        model = Truck
        fields = [
            "plate",
            "model",
            "brand",
            "year",
            "tank_capacity_liters",
            "current_odometer",
            "acquisition_date",
            "status",
            "notes",
        ]
        widgets = {
            "plate": forms.TextInput(attrs={"class": T_INPUT}),
            "model": forms.TextInput(attrs={"class": T_INPUT}),
            "brand": forms.TextInput(attrs={"class": T_INPUT}),
            "acquisition_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "status": forms.Select(attrs={"class": T_SELECT}),
            "notes": forms.Textarea(attrs={"class": T_INPUT + " min-h-[72px]", "rows": 2}),
        }

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)

        year_initial = ""
        if self.instance.pk and self.instance.year is not None:
            year_initial = str(self.instance.year)

        self.fields["year"] = forms.CharField(
            label="Ano",
            required=False,
            initial=year_initial,
            widget=forms.TextInput(
                attrs={
                    "class": T_INPUT + " int-br placeholder:text-slate-400",
                    "placeholder": "2020",
                    "inputmode": "numeric",
                    "maxlength": "4",
                    "autocomplete": "off",
                }
            ),
        )

        tank_initial = ""
        if self.instance.pk and self.instance.tank_capacity_liters is not None:
            tank_initial = format_br_decimal(self.instance.tank_capacity_liters, places=2)

        self.fields["tank_capacity_liters"] = forms.CharField(
            label="Capacidade do tanque (L)",
            required=False,
            help_text="Formato brasileiro — ex.: 10.000,50",
            initial=tank_initial,
            widget=forms.TextInput(
                attrs={
                    "class": MONEY_INPUT_CLASS,
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )

        odo_initial = ""
        if self.instance.pk and self.instance.current_odometer is not None:
            odo_initial = format_br_decimal(self.instance.current_odometer, places=2)

        self.fields["current_odometer"] = forms.CharField(
            label="Quilometragem atual",
            required=False,
            help_text="Formato brasileiro — ex.: 125.430,50",
            initial=odo_initial,
            widget=forms.TextInput(
                attrs={
                    "class": MONEY_INPUT_CLASS,
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )

        finalize_company_form(self)

    def clean(self):
        return super().clean()

    def clean_year(self):
        raw = self.cleaned_data.get("year", "")
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            return None
        s = str(raw).strip().replace(".", "").replace(",", "")
        if not s.isdigit():
            raise forms.ValidationError("Indique um ano válido (ex.: 2024).")
        y = int(s)
        if y < 1900 or y > 2100:
            raise forms.ValidationError("Ano fora do intervalo esperado.")
        return y

    def _parse_optional_money(self, field_name: str, label: str) -> Decimal | None:
        raw = self.cleaned_data.get(field_name, "")
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            return None
        try:
            v = parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e
        if v < 0:
            raise forms.ValidationError(f"{label} não pode ser negativo.")
        return v

    def clean_tank_capacity_liters(self):
        return self._parse_optional_money("tank_capacity_liters", "A capacidade")

    def clean_current_odometer(self):
        return self._parse_optional_money("current_odometer", "A quilometragem")

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        obj.year = self.cleaned_data.get("year")
        obj.tank_capacity_liters = self.cleaned_data.get("tank_capacity_liters")
        obj.current_odometer = self.cleaned_data.get("current_odometer")
        if commit:
            obj.save()
        return obj
