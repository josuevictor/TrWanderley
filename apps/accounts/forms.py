from django.contrib.auth.forms import AuthenticationForm


class TailwindAuthenticationForm(AuthenticationForm):
    """Campos com classes Tailwind (CDN no base_app)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base = (
            "mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-base md:text-sm "
            "dark:border-slate-700 dark:bg-slate-800"
        )
        self.fields["username"].widget.attrs.update(
            {"class": base, "placeholder": "", "autocomplete": "username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": base, "placeholder": "", "autocomplete": "current-password"}
        )
