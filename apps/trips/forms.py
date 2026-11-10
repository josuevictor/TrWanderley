from decimal import Decimal

from django import forms
from django.db.models import Q

from apps.core.money import format_br_decimal, parse_br_decimal
from apps.customers.models import Customer, CustomerDeliveryPlace
from apps.employees.models import Employee, EmployeeStatus
from apps.finance.forms import T_INPUT, T_SELECT
from apps.finance.models import PaymentMethod
from apps.trucks.models import Truck, TruckStatus

from .models import Trip

MONEY_INPUT_CLASS = T_INPUT + " money-br placeholder:text-slate-400"
MONEY_HELP = "Formato brasileiro: 1.234,56 (milhar com ponto, centavos com vírgula)."
VOL_CLASS = T_INPUT + " dec-br-3 placeholder:text-slate-400"


class TripForm(forms.ModelForm):
    """
    Decimais monetários e volume como texto (vírgula BR), com parse no servidor
    alinhado à máscara global em static/js/br-inputs.js.
    """

    class Meta:
        model = Trip
        fields = [
            "trip_date",
            "trip_time",
            "truck",
            "driver",
            "customer",
            "delivery_place_ref",
            "delivery_place",
            "volume_m3",
            "trip_count",
            "amount_charged",
            "payment_method",
            "payment_status",
            "notes",
        ]
        widgets = {
            "trip_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "trip_time": forms.TimeInput(attrs={"type": "time", "class": T_INPUT}),
            "truck": forms.Select(attrs={"class": T_SELECT}),
            "driver": forms.Select(attrs={"class": T_SELECT}),
            "customer": forms.Select(attrs={"class": T_SELECT}),
            "delivery_place_ref": forms.Select(attrs={"class": T_SELECT}),
            "delivery_place": forms.TextInput(attrs={"class": T_INPUT}),
            "payment_method": forms.Select(attrs={"class": T_SELECT}),
            "payment_status": forms.Select(attrs={"class": T_SELECT}),
            "notes": forms.Textarea(attrs={"class": T_INPUT + " min-h-[72px]", "rows": 2}),
        }

    def __init__(self, *args, company, user, driver_employee=None, **kwargs):
        self.company = company
        self.user = user
        self.driver_employee = driver_employee
        super().__init__(*args, **kwargs)

        truck_q = Q(company=company, status=TruckStatus.ACTIVE)
        if self.instance.pk and self.instance.truck_id:
            truck_q |= Q(pk=self.instance.truck_id)
        self.fields["truck"].queryset = (
            Truck.objects.filter(truck_q).distinct().order_by("plate")
        )
        self.fields["customer"].queryset = Customer.objects.filter(company=company).order_by("name")

        self.fields["delivery_place_ref"].queryset = CustomerDeliveryPlace.objects.filter(
            customer__company=company
        ).select_related("customer")
        self.fields["delivery_place_ref"].required = False
        self.fields["delivery_place_ref"].label = "Local de entrega (cadastro do cliente)"
        self.fields["delivery_place_ref"].help_text = (
            "Opcional. Escolha um local já cadastrado em Clientes ou preencha o campo livre abaixo."
        )
        self.fields["delivery_place"].label = "Local de entrega (livre)"
        self.fields["delivery_place"].help_text = (
            "Use quando não houver local cadastrado ou para complementar. Se escolher um cadastrado acima, "
            "este campo é preenchido automaticamente."
        )
        if "driver" in self.fields:
            drv_q = Q(company=company, status=EmployeeStatus.ACTIVE)
            if self.instance.pk and self.instance.driver_id:
                drv_q |= Q(pk=self.instance.driver_id)
            self.fields["driver"].queryset = (
                Employee.objects.filter(drv_q).distinct().order_by("name")
            )
        self.fields["payment_method"].queryset = PaymentMethod.objects.filter(
            company=company, is_active=True
        ).order_by("name")
        self.fields["payment_method"].required = False

        if driver_employee is not None:
            del self.fields["driver"]
            if driver_employee.truck_id:
                self.fields["truck"].queryset = Truck.objects.filter(
                    pk=driver_employee.truck_id,
                    company=company,
                )

        count_initial = ""
        if self.instance.pk and self.instance.trip_count is not None:
            count_initial = str(self.instance.trip_count)

        self.fields["trip_count"] = forms.CharField(
            label="Quantidade de viagens",
            required=True,
            min_length=1,
            initial=count_initial or "1",
            widget=forms.TextInput(
                attrs={
                    "class": T_INPUT + " int-br placeholder:text-slate-400",
                    "placeholder": "1",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                }
            ),
        )

        vol_initial = ""
        if self.instance.pk and self.instance.volume_m3 is not None:
            vol_initial = format_br_decimal(self.instance.volume_m3, places=3)

        self.fields["volume_m3"] = forms.CharField(
            label="Volume (m³)",
            required=False,
            help_text="Opcional. Até 3 casas decimais — ex.: 12,5 ou 10,250.",
            initial=vol_initial,
            widget=forms.TextInput(
                attrs={
                    "class": VOL_CLASS,
                    "placeholder": "0,000",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )

        amt_initial = ""
        if self.instance.pk and self.instance.amount_charged is not None:
            amt_initial = format_br_decimal(self.instance.amount_charged, places=2)

        cust = self.instance.customer_id if self.instance.pk else None
        if cust:
            self.fields["delivery_place_ref"].queryset = CustomerDeliveryPlace.objects.filter(
                customer_id=cust
            )
        else:
            self.fields["delivery_place_ref"].queryset = CustomerDeliveryPlace.objects.none()

        if self.instance.pk and self.instance.customer_id and not self.instance.delivery_place_ref_id:
            addr = (self.instance.delivery_place or "").strip()
            if addr:
                match = CustomerDeliveryPlace.objects.filter(
                    customer_id=self.instance.customer_id, address_line=addr
                ).first()
                if match:
                    self.initial["delivery_place_ref"] = match.pk

        self.fields["amount_charged"] = forms.CharField(
            label="Valor cobrado",
            required=True,
            help_text=MONEY_HELP,
            initial=amt_initial,
            widget=forms.TextInput(
                attrs={
                    "class": MONEY_INPUT_CLASS,
                    "placeholder": "0,00",
                    "inputmode": "decimal",
                    "autocomplete": "off",
                }
            ),
        )

    def _parse_optional_volume(self) -> Decimal | None:
        raw = self.cleaned_data.get("volume_m3", "")
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return None
        try:
            v = parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e
        if v < 0:
            raise forms.ValidationError("O volume não pode ser negativo.")
        return v

    def clean_volume_m3(self):
        return self._parse_optional_volume()

    def clean_amount_charged(self):
        raw = self.cleaned_data.get("amount_charged", "")
        if raw is None or (isinstance(raw, str) and not str(raw).strip()):
            raise forms.ValidationError("Indique o valor cobrado.")
        try:
            v = parse_br_decimal(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e)) from e
        if v < 0:
            raise forms.ValidationError("O valor cobrado não pode ser negativo.")
        return v

    def clean_trip_count(self):
        raw = self.cleaned_data.get("trip_count", "")
        s = str(raw or "").strip().replace(".", "").replace(",", "")
        if not s:
            raise forms.ValidationError("Indique a quantidade de viagens.")
        if not s.isdigit():
            raise forms.ValidationError("Use apenas números inteiros (ex.: 5).")
        n = int(s)
        if n < 1:
            raise forms.ValidationError("Deve ser pelo menos 1.")
        return n

    def clean(self):
        data = super().clean()
        customer = data.get("customer")
        dref = data.get("delivery_place_ref")
        free = (data.get("delivery_place") or "").strip()

        if dref and customer and dref.customer_id != customer.pk:
            self.add_error("delivery_place_ref", "Este local não pertence ao cliente selecionado.")
        if dref:
            data["delivery_place"] = dref.address_line
        elif not free:
            # Pelo menos um dos dois
            self.add_error(
                "delivery_place",
                "Indique o local de entrega (cadastrado ou texto livre).",
            )
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.company = self.company
        if self.driver_employee is not None:
            obj.driver = self.driver_employee
        obj.volume_m3 = self.cleaned_data.get("volume_m3")
        obj.trip_count = self.cleaned_data["trip_count"]
        obj.amount_charged = self.cleaned_data["amount_charged"]
        dref = self.cleaned_data.get("delivery_place_ref")
        if dref:
            obj.delivery_place_ref = dref
            obj.delivery_place = dref.address_line
        else:
            obj.delivery_place_ref = None
            obj.delivery_place = (self.cleaned_data.get("delivery_place") or "").strip()
        if commit:
            obj.save()
        return obj
