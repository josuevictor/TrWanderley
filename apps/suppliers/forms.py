from django import forms

from apps.core.form_utils import finalize_company_form
from apps.finance.forms import T_INPUT, T_SELECT

from .models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "supplier_type", "tax_id", "phone", "address", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={"class": T_INPUT}),
            "supplier_type": forms.Select(attrs={"class": T_SELECT}),
            "tax_id": forms.TextInput(attrs={"class": T_INPUT}),
            "phone": forms.TextInput(attrs={"class": T_INPUT}),
            "address": forms.TextInput(attrs={"class": T_INPUT}),
            "notes": forms.Textarea(attrs={"class": T_INPUT + " min-h-[72px]", "rows": 2}),
        }

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        finalize_company_form(self)

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        if commit:
            obj.save()
        return obj
