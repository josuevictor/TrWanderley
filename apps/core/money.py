"""Parse e formatação de valores monetários (padrão BR no input)."""

from decimal import Decimal, InvalidOperation


def parse_br_decimal(value) -> Decimal | None:
    """
    Aceita ex.: "1.234,56", "1234,56", "1234.56", " 1 234,56 ", "R$ 100,00".
    Devolve None se vazio e obrigatoriamente None for allowed upstream.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("\u00a0", " ").replace(" ", "")
    for prefix in ("R$", "r$", "$"):
        if s.startswith(prefix):
            s = s[len(prefix) :].strip()
    if not s:
        return None
    # Formato BR: pontos milhares, vírgula decimal
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # apenas pontos: pode ser decimal US ou milhares BR sem decimais
        if s.count(".") > 1:
            s = s.replace(".", "")
        elif s.count(".") == 1:
            parts = s.split(".")
            if len(parts[1]) == 3:
                s = s.replace(".", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Valor numérico inválido: {value!r}")


def format_br_decimal(value: Decimal | None, places: int = 2) -> str:
    if value is None:
        return ""
    q = Decimal("1").scaleb(-places)  # 10^-places
    v = value.quantize(q)
    s = f"{v:.{places}f}"
    intp, _, frac = s.partition(".")
    # milhares com ponto
    sign = ""
    if intp.startswith("-"):
        sign = "-"
        intp = intp[1:]
    rev = intp[::-1]
    chunks = [rev[i : i + 3] for i in range(0, len(rev), 3)]
    intp_fmt = ".".join(c[::-1] for c in reversed(chunks))
    return f"{sign}{intp_fmt},{frac}"
