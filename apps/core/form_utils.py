"""Utilitários partilhados por formulários da app."""

from __future__ import annotations

from django import forms


def optionalize_form_fields(form: forms.BaseForm) -> None:
    """Todos os campos opcionais no formulário (sem asterisco / required HTML)."""
    for field in form.fields.values():
        field.required = False
        attrs = getattr(field.widget, "attrs", None)
        if isinstance(attrs, dict):
            attrs.pop("required", None)


def bind_company_on_instance(form: forms.ModelForm) -> None:
    """Evita erro «Empresa obrigatória.» na validação do modelo antes do save."""
    company = getattr(form, "company", None)
    if company and form.instance is not None:
        form.instance.company = company


def finalize_company_form(form: forms.ModelForm) -> None:
    """Campos opcionais + empresa na instância (chamar no fim do ``__init__``)."""
    optionalize_form_fields(form)
    bind_company_on_instance(form)
