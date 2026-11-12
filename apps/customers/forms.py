from django import forms
from django.forms import inlineformset_factory

from apps.core.form_utils import finalize_company_form
from apps.finance.forms import T_INPUT

from .models import Customer, CustomerDeliveryPlace


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "tax_id", "phone", "email", "address", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={"class": T_INPUT}),
            "tax_id": forms.TextInput(attrs={"class": T_INPUT}),
            "phone": forms.TextInput(attrs={"class": T_INPUT}),
            "email": forms.EmailInput(attrs={"class": T_INPUT}),
            "address": forms.TextInput(attrs={"class": T_INPUT}),
            "notes": forms.Textarea(attrs={"class": T_INPUT + " min-h-[72px]", "rows": 2}),
        }

    def __init__(self, *args, company, instance=None, **kwargs):
        self.company = company
        super().__init__(*args, instance=instance, **kwargs)
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


class BaseCustomerDeliveryPlaceFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        for form in self.forms:
            cd = form.cleaned_data
            if not cd or cd.get("DELETE"):
                continue
            addr = (cd.get("address_line") or "").strip()
            label = (cd.get("label") or "").strip()
            if not addr and not label:
                continue


def delivery_places_formset_factory(*, customer: Customer | None, data=None, prefix="places"):
    """Uma linha extra só quando o cliente ainda não tem locais (evita dois vazios ao editar)."""
    extra = 1
    if customer and customer.pk and customer.delivery_places.exists():
        extra = 0
    FormSetCls = inlineformset_factory(
        Customer,
        CustomerDeliveryPlace,
        formset=BaseCustomerDeliveryPlaceFormSet,
        fields=("label", "address_line", "sort_order"),
        extra=extra,
        can_delete=True,
        min_num=0,
        widgets={
            "label": forms.TextInput(
                attrs={"class": T_INPUT, "placeholder": "Ex.: Obra Norte", "autocomplete": "off"}
            ),
            "address_line": forms.TextInput(
                attrs={
                    "class": T_INPUT,
                    "placeholder": "Endereço ou referência do local",
                    "autocomplete": "off",
                }
            ),
            "sort_order": forms.NumberInput(
                attrs={
                    "class": T_INPUT + " int-br",
                    "placeholder": "0",
                    "min": 0,
                    "inputmode": "numeric",
                }
            ),
        },
        labels={
            "label": "Nome do local",
            "address_line": "Endereço / local",
            "sort_order": "Ordem",
        },
    )
    if customer is not None:
        if data is not None:
            return FormSetCls(data, instance=customer, prefix=prefix)
        return FormSetCls(instance=customer, prefix=prefix)
    if data is not None:
        return FormSetCls(data, prefix=prefix)
    return FormSetCls(prefix=prefix)
