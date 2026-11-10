"""Formulários financeiros — classes Tailwind para inputs."""

import re
import unicodedata

from django import forms
from django.db.models import Q

from apps.core.money import format_br_decimal, parse_br_decimal

from .constants import PROTECTED_CATEGORY_SLUGS
from .models import (
    CashMovement,
    CashMovementKind,
    FinancialAccount,
    FinancialCategory,
    FinancialCategoryKind,
    FinancialEntry,
    FinancialEntryType,
    PaymentMethod,
)

# text-base em <md: evita zoom automático no iOS ao focar (fonte mín. ~16px)
T_INPUT = (
    "w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-base md:text-sm "
    "text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 "
    "dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
)
T_SELECT = T_INPUT
T_CHECK = "h-4 w-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"


def _slugify_from_name(name: str, max_length: int = 60) -> str:
    """ASCII slug a partir do nome (amigável para URLs/código interno)."""
    name = (name or "").strip()
    if not name:
        return "categoria"
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    if not s:
        return "categoria"
    return s[:max_length]


class FinancialCategoryForm(forms.ModelForm):
    class Meta:
        model = FinancialCategory
        fields = ["name", "kind", "is_active"]

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": T_INPUT})
        self.fields["kind"].widget.attrs.update({"class": T_SELECT})
        self.fields["is_active"].widget.attrs.update({"class": T_CHECK})
        self.fields["name"].help_text = "O código interno é gerado automaticamente a partir do nome."

    def _assign_slug(self, obj: FinancialCategory) -> None:
        if obj.slug and obj.slug in PROTECTED_CATEGORY_SLUGS:
            return
        base = _slugify_from_name(obj.name)
        candidate = base
        n = 2
        qs = FinancialCategory.objects.filter(company=obj.company, kind=obj.kind)
        if obj.pk:
            qs = qs.exclude(pk=obj.pk)
        while qs.filter(slug=candidate).exists():
            suffix = f"-{n}"
            candidate = (base[: max(0, 60 - len(suffix))] + suffix)[:60]
            n += 1
        obj.slug = candidate

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        self._assign_slug(obj)
        if commit:
            obj.save()
        return obj


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ["name", "is_active"]

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": T_INPUT})
        self.fields["is_active"].widget.attrs.update({"class": T_CHECK})

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        if commit:
            obj.save()
        return obj


class FinancialAccountForm(forms.ModelForm):
    class Meta:
        model = FinancialAccount
        fields = ["name", "kind", "is_active"]

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"class": T_INPUT})
        self.fields["kind"].widget.attrs.update({"class": T_SELECT})
        self.fields["is_active"].widget.attrs.update({"class": T_CHECK})

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        if commit:
            obj.save()
        return obj


MONEY_HELP_BR = "Valores em reais, formato brasileiro: 1.234,56."


class FinancialEntryForm(forms.ModelForm):
    class Meta:
        model = FinancialEntry
        fields = [
            "entry_type",
            "description",
            "category",
            "amount",
            "competence_date",
            "due_date",
            "payment_method",
            "default_account",
            "notes",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "competence_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "notes": forms.Textarea(
                attrs={"class": T_INPUT + " min-h-[80px]", "rows": 3}
            ),
        }

    def __init__(self, *args, company, user=None, **kwargs):
        self.company = company
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["description"].widget.attrs.update({"class": T_INPUT})

        amt_initial = ""
        if self.instance.pk and self.instance.amount is not None:
            amt_initial = format_br_decimal(self.instance.amount, places=2)
        self.fields["amount"] = forms.CharField(
            label="Valor",
            help_text=MONEY_HELP_BR,
            required=True,
            initial=amt_initial,
            widget=forms.TextInput(
                attrs={
                    "class": T_INPUT + " money-br placeholder:text-slate-400",
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )
        self.fields["entry_type"].widget.attrs.update({"class": T_SELECT})
        cq = Q(company=company, is_active=True)
        if self.instance.pk and self.instance.category_id:
            cq |= Q(pk=self.instance.category_id)
        self.fields["category"].queryset = FinancialCategory.objects.filter(cq).distinct().order_by(
            "kind", "name"
        )
        self.fields["category"].widget.attrs.update({"class": T_SELECT})
        pq = Q(company=company, is_active=True)
        if self.instance.pk and self.instance.payment_method_id:
            pq |= Q(pk=self.instance.payment_method_id)
        self.fields["payment_method"].queryset = PaymentMethod.objects.filter(pq).distinct().order_by(
            "name"
        )
        self.fields["payment_method"].required = False
        self.fields["payment_method"].widget.attrs.update({"class": T_SELECT})
        aq = Q(company=company, is_active=True)
        if self.instance.pk and self.instance.default_account_id:
            aq |= Q(pk=self.instance.default_account_id)
        self.fields["default_account"].queryset = FinancialAccount.objects.filter(aq).distinct().order_by(
            "name"
        )
        self.fields["default_account"].required = False
        self.fields["default_account"].widget.attrs.update({"class": T_SELECT})

    def clean_category(self):
        cat = self.cleaned_data["category"]
        if cat.company_id != self.company.id:
            raise forms.ValidationError("Categoria inválida.")
        return cat

    def clean_amount(self):
        raw = self.cleaned_data.get("amount", "")
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            raise forms.ValidationError("Indique o valor.")
        try:
            v = parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e
        if v <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero.")
        return v

    def clean(self):
        cleaned = super().clean()
        et = cleaned.get("entry_type")
        cat = cleaned.get("category")
        if et and cat:
            want = (
                FinancialCategoryKind.INCOME
                if et == FinancialEntryType.INCOME
                else FinancialCategoryKind.EXPENSE
            )
            if cat.kind != want:
                self.add_error(
                    "category",
                    "A categoria deve ser do mesmo tipo que o lançamento (receita/despesa).",
                )
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
            if self.user and self.user.is_authenticated:
                obj.created_by = self.user
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        obj.amount = self.cleaned_data["amount"]
        if commit:
            obj.save()
        return obj


class CashMovementForm(forms.ModelForm):
    class Meta:
        model = CashMovement
        fields = ["kind", "financial_account", "amount", "movement_date", "payment_method", "memo"]
        widgets = {
            "movement_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "memo": forms.TextInput(attrs={"class": T_INPUT}),
        }

    def __init__(self, *args, company, user=None, **kwargs):
        self.company = company
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["kind"].choices = [
            (CashMovementKind.RECEIPT, "Recebimento"),
            (CashMovementKind.PAYMENT, "Pagamento"),
        ]
        self.fields["kind"].widget.attrs.update({"class": T_SELECT})

        amt_initial = ""
        if self.instance.pk and self.instance.amount is not None:
            amt_initial = format_br_decimal(self.instance.amount, places=2)
        self.fields["amount"] = forms.CharField(
            label="Valor",
            help_text=MONEY_HELP_BR,
            required=True,
            initial=amt_initial,
            widget=forms.TextInput(
                attrs={
                    "class": T_INPUT + " money-br placeholder:text-slate-400",
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )
        fq = Q(company=company, is_active=True)
        if self.instance.pk and self.instance.financial_account_id:
            fq |= Q(pk=self.instance.financial_account_id)
        self.fields["financial_account"].queryset = FinancialAccount.objects.filter(fq).distinct().order_by(
            "name"
        )
        self.fields["financial_account"].widget.attrs.update({"class": T_SELECT})
        pmq = Q(company=company, is_active=True)
        if self.instance.pk and self.instance.payment_method_id:
            pmq |= Q(pk=self.instance.payment_method_id)
        self.fields["payment_method"].queryset = PaymentMethod.objects.filter(pmq).distinct().order_by(
            "name"
        )
        self.fields["payment_method"].required = False
        self.fields["payment_method"].widget.attrs.update({"class": T_SELECT})

    def clean_financial_account(self):
        acc = self.cleaned_data["financial_account"]
        if acc.company_id != self.company.id:
            raise forms.ValidationError("Conta inválida.")
        return acc

    def clean_amount(self):
        raw = self.cleaned_data.get("amount", "")
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            raise forms.ValidationError("Indique o valor.")
        try:
            v = parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e
        if v <= 0:
            raise forms.ValidationError("O valor deve ser maior que zero.")
        return v

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
            if self.user and self.user.is_authenticated:
                obj.created_by = self.user
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        obj.amount = self.cleaned_data["amount"]
        if commit:
            obj.save()
        return obj
