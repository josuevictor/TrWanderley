# Sistema de gestão — caminhão-pipa

Monólito Django (templates + DRF), PostgreSQL, Docker.

## Requisitos

- Python 3.11+
- PostgreSQL 16 (ou Docker)

## Ambiente local

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Sem PostgreSQL local: usar SQLite
export USE_SQLITE=1
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Login: [http://127.0.0.1:8000/conta/entrar/](http://127.0.0.1:8000/conta/entrar/)
- Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Primeiro utilizador / empresa

1. Crie uma **Company** e um **CompanyMembership** do seu utilizador (Administrador ou Gerente).
2. Com **uma só** empresa, a sessão escolhe-a automaticamente; com várias, use o seletor no topo.

### Motoristas (perfil Driver)

1. Registe o funcionário (menu **Funcionários** ou admin).
2. No admin, no **Employee**, associe o campo **Utilizador (login)** ao user do motorista.
3. O motorista vê apenas as **suas** viagens e abastecimentos e não vê o módulo financeiro completo no menu.

## URLs principais (MVP)

| Área | Caminho |
|------|---------|
| Painel | `/` |
| Financeiro | `/financeiro/` |

Tutorial detalhado (conceitos, categorias, lançamentos, caixa): [docs/TUTORIAL_FINANCEIRO.md](docs/TUTORIAL_FINANCEIRO.md).
| Caminhões | `/frota/` |
| Funcionários | `/funcionarios/` |
| Clientes | `/clientes/` |
| Fornecedores | `/fornecedores/` |
| Receitas (viagens) | `/financeiro/receitas/` (redireciona de `/viagens/`) |
| Combustível | `/combustivel/` |
| Manutenção | `/manutencao/` |

Viagens, combustível e manutenção geram **lançamentos de competência** no financeiro (categorias com slug `trip_income`, `fuel`, `maintenance`), sem duplicar ao editar o mesmo registo.

## PWA (instalação)

O layout inclui **manifest** (`static/manifest.webmanifest`) e registo de **service worker** (`static/sw.js`). Para ícones na tela inicial, acrescente ficheiros em `static/icons/` e atualize o manifest.

## Docker

```bash
cp .env.example .env
# Defina SECRET_KEY e ALLOWED_HOSTS no .env para produção
docker compose up --build
```

## Testes

```bash
USE_SQLITE=1 DJANGO_SETTINGS_MODULE=config.settings.development python manage.py test
```

### Dados de demonstração (caminhões fictícios)

Com pelo menos uma empresa criada no admin:

```bash
USE_SQLITE=1 DJANGO_SETTINGS_MODULE=config.settings.development python manage.py seed_demo_trucks
USE_SQLITE=1 DJANGO_SETTINGS_MODULE=config.settings.development python manage.py seed_demo_finance
# ou: --company-id 1   ou   --company-name "Nome exato"
```

Cria duas matrículas fictícias (`DMO-1A23`, `DMO-9Z87`) se ainda não existirem para essa empresa.

## Estrutura

- `config/` — settings, URLs, WSGI/ASGI
- `apps/` — módulos
- `templates/` — Django templates (Tailwind CDN, Alpine, HTMX)
- `static/` / `media/`

## Pós-MVP (ideias)

- UI para alocar recebimentos/pagamentos a lançamentos (`EntryPaymentAllocation`)
- Transferências entre contas e relatórios PDF/Excel
- API DRF versionada e auditoria detalhada
