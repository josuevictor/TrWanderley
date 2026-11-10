"""Constantes do módulo financeiro (evita imports circulares)."""

# Slugs criados por ensure_default_categories — não eliminar (operacional).
PROTECTED_CATEGORY_SLUGS = frozenset(
    {
        "trip_income",
        "service_extra",
        "other_income",
        "fuel",
        "maintenance",
        "tires",
        "salary",
        "other_expense",
    }
)
