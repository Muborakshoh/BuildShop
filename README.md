# BuildShop

Modular monolith for a construction materials online store.

## Stack

- Backend: Python, FastAPI, Uvicorn
- Database: PostgreSQL
- ORM: SQLAlchemy
- Auth: JWT access and refresh tokens
- Passwords: bcrypt via Passlib
- Frontend: HTML, CSS, Vanilla JS with Fetch API
- Runtime: Docker Compose

## Project Structure

```text
/app
  /auth
    router.py
    service.py
    repository.py
    schemas.py
  /users
    router.py
    service.py
    repository.py
    models.py
    schemas.py
  /products
    router.py
    service.py
    repository.py
    models.py
    schemas.py
  /orders
    router.py
    service.py
    repository.py
    models.py
    schemas.py
  /inventory
    router.py
    service.py
    repository.py
    models.py
    schemas.py
  /cashier
    router.py
    service.py
    repository.py
    models.py
    schemas.py
  /core
    config.py
    dependencies.py
    security.py
  /db
    session.py
  /static
    index.html
    /pages
    /css
    /js
  main.py
Dockerfile
docker-compose.yml
requirements.txt
.env.example
```

## Run With Docker

```bash
docker compose -p buildshop up --build
```

Optional first admin:

```bash
FIRST_ADMIN_EMAIL=admin@example.com FIRST_ADMIN_PASSWORD=strongpass123 docker compose -p buildshop up --build
```

Open:

- Frontend: http://localhost:8000
- Cashier: http://localhost:8000/pages/cashier.html
- Swagger: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

PostgreSQL is published on port `5432`:

```text
Host: 127.0.0.1
Port: 5432
Database: buildshop
User: buildshop
Password: buildshop_password
```

Connection string:

```text
postgresql://buildshop:buildshop_password@127.0.0.1:5432/buildshop
```

## Run Locally Without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

For local mode, PostgreSQL must already be running and match `DATABASE_URL` in `.env`.

Tables are created at application startup with SQLAlchemy metadata. For a real production rollout, add Alembic migrations before changing schemas.

If `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD` are set in `.env`, the app creates that admin once on startup.

## API Examples

Register:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","full_name":"Demo User","password":"strongpass123"}'
```

Login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"strongpass123"}'
```

Refresh tokens:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

List products:

```bash
curl "http://localhost:8000/api/products?search=cement&in_stock=true"
```

Create category as admin:

```bash
curl -X POST http://localhost:8000/api/categories \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Dry Mixes","slug":"dry-mixes","description":"Cement, plaster and concrete mixes"}'
```

Create product as admin:

```bash
curl -X POST http://localhost:8000/api/products \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"category_id":1,"name":"Portland Cement 50kg","slug":"portland-cement-50kg","description":"General purpose cement for construction work","price":"520.00","image_url":null,"initial_stock":100}'
```

Create order:

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"delivery_address":"Moscow, Lenina 10","items":[{"product_id":1,"quantity":2}]}'
```

Update inventory as admin:

```bash
curl -X POST http://localhost:8000/api/inventory/1/adjust \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"delta":25}'
```

Open a cash shift as `seller`, `manager`, or `admin`:

```bash
curl -X POST http://localhost:8000/api/cashier/shifts/open \
  -H "Authorization: Bearer <cashier_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"register_name":"Cash Register 1","opening_cash":"1000.00"}'
```

Create an in-store sale:

```bash
curl -X POST http://localhost:8000/api/cashier/sales \
  -H "Authorization: Bearer <cashier_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"payment_method":"card","card_amount":"1040.00","items":[{"product_id":1,"quantity":2}]}'
```

Close a shift as `manager` or `admin`:

```bash
curl -X POST http://localhost:8000/api/cashier/shifts/1/close \
  -H "Authorization: Bearer <manager_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"actual_cash":"1000.00"}'
```

## Main Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/users/me`
- `GET /api/categories`
- `POST /api/categories`
- `GET /api/products`
- `GET /api/products/{product_id}`
- `POST /api/products`
- `PATCH /api/products/{product_id}`
- `DELETE /api/products/{product_id}`
- `POST /api/orders`
- `GET /api/orders`
- `GET /api/orders/{order_id}`
- `PATCH /api/orders/{order_id}/status`
- `GET /api/inventory`
- `PUT /api/inventory/{product_id}`
- `POST /api/inventory/{product_id}/adjust`
- `POST /api/cashier/shifts/open`
- `GET /api/cashier/shifts/current`
- `POST /api/cashier/shifts/{shift_id}/close`
- `POST /api/cashier/sales`
- `POST /api/cashier/refunds`
- `GET /api/cashier/shifts/{shift_id}/summary`

## Notes

- SQL injection protection is handled by SQLAlchemy query construction.
- Request and response validation is handled by Pydantic schemas.
- Protected endpoints use FastAPI dependencies for JWT validation.
- Admin-only endpoints use a role dependency.
- Cashier endpoints use `seller`, `manager`, and `admin` roles. Sellers can open shifts and sell; managers/admins can close shifts, view summaries, and process refunds.
- This is a modular monolith: one deployable application, split by business domains.
