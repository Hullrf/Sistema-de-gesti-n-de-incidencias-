# Wava — Pasarela de pago (Colombia)

Resumen técnico de la documentación oficial de Wava (https://docs.wava.co/) para
una eventual integración de cobros (p. ej. planes de pago, suscripciones o
cobro de servicios) en este sistema de gestión de incidencias.

> Este documento es una guía de referencia, no una integración ya implementada.
> Actualmente el proyecto no tiene ningún módulo de pagos.

## 1. ¿Qué es Wava?

Wava Technologies es una fintech colombiana que ofrece una API unificada de
procesamiento de pagos. Permite cobrar a través de billeteras digitales y
medios alternativos con una sola integración:

- **Nequi** (COP) — pago por notificación push al celular
- **Daviplata** (COP) — verificación por código OTP
- **Breb / Transfiya A2A** (COP) — transferencia bancaria instantánea o QR
- **Stripe** — tarjetas, múltiples monedas

También ofrece **links de pago** (URLs para cobrar sin checkout propio) y una
**API de Partners** para plataformas que administran múltiples comercios.

## 2. URLs base y entornos

| Entorno | Base URL |
|---|---|
| Producción | `https://api.wava.co/v1` |
| Sandbox / desarrollo | `https://api.dev.wava.co/v1` |

- En sandbox no se mueve dinero real (transacciones simuladas), acepta datos
  de prueba y tiene rate limiting más permisivo.
- Credenciales de sandbox: https://app.dev.wava.co
- Credenciales de producción: https://app.wava.co (requiere validación de
  compliance / documentación del negocio)
- Las llaves son distintas por entorno; **nunca** usar credenciales de
  producción en desarrollo.

## 3. Autenticación

**Como comercio (merchant):** un único header `merchant-key`.

```
GET /v1/orders/paymentGateways
merchant-key: YOUR_MERCHANT_KEY
```

**Como partner** (gestiona varios comercios): header adicional de dos
factores.

```
POST /v1/orders
merchant-key: STORE_MERCHANT_KEY
X-API-Key: YOUR_PARTNER_API_KEY
X-API-Secret: YOUR_PARTNER_SECRET_KEY
```

Buenas prácticas: guardar las llaves como variables de entorno o en un
secrets manager, nunca en el repositorio ni en código cliente. Reportar
compromisos de credenciales a `soporte@wava.co`.

## 4. Descubrimiento de pasarelas

`GET /v1/orders/paymentGateways` (header `merchant-key`) devuelve las
pasarelas activas para el comercio, su `id_payment_gateway` y los campos
requeridos, para no hardcodear IDs de gateway.

```json
{
  "data": [
    {
      "id_payment_gateway": 1,
      "name": "Nequi",
      "required_fields": ["phone_number"],
      "icon": "https://wava-assets.s3.us-east-1.amazonaws.com/payment-gateways/nequi-icon.png"
    }
  ]
}
```

## 5. Crear una orden (cobro)

`POST /v1/orders` — header `merchant-key`.

Campos obligatorios: `amount`, `description`, `currency` (`COP` para
pasarelas colombianas), `shopper.first_name`, `shopper.last_name`,
`shopper.email`, `shopper.phone_number`, `shopper.country` (`CO`),
`shopper.id_number` (cédula), `shopper.id_type` (según catálogo de tipos de
documento), `payment_gateway.id_payment_gateway`.

Opcionales: `order_key` (idempotencia), `redirect_link`,
`redirect_link_cancel`, `redirect_link_failure`.

```bash
curl -X POST "https://api.wava.co/v1/orders" \
  -H "merchant-key: YOUR_MERCHANT_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50000,
    "description": "Suscripción premium",
    "currency": "COP",
    "shopper": {
      "first_name": "Juan",
      "last_name": "Perez",
      "email": "juan@email.com",
      "phone_number": "+573001234567",
      "country": "CO",
      "id_number": "1234567890",
      "id_type": 1
    },
    "payment_gateway": { "id_payment_gateway": 1 },
    "order_key": "order-12345"
  }'
```

Tipos de documento (`allowed_documents`): `1` CC (Cédula de Ciudadanía),
`2` CE (Cédula de Extranjería), `3` TI (Tarjeta de Identidad).

## 6. Ciclo de vida de la orden

```
pending → processing → confirmed (o cancelled) → refunded
```

- **pending**: creada, sin pago iniciado
- **processing**: el comprador está confirmando (push, OTP, QR, tarjeta)
- **confirmed**: pago exitoso; los fondos liquidan en ~36 horas
- **cancelled**: rechazada, expiró (timeout) o se canceló por API
- **refunded**: reembolso procesado

Timeouts aproximados: Nequi/Daviplata ~5 min, Breb ~15 min. Solo se puede
cancelar por API una orden en `pending` o `processing`.

**Seguimiento:** preferir webhooks; como respaldo, polling a
`GET /v1/orders/{order_id}` (header `merchant-key`) cada 3–5 s para no
disparar rate limiting.

## 7. Webhooks

- Configurar la URL en el Dashboard → Settings → Integrations → API.
- El endpoint debe aceptar `POST`, responder `200` en menos de 5 s, y estar
  en HTTPS en producción.
- Reintentos: hasta 3 intentos, ~1 s de separación, timeout de 5 s por
  intento. Los 4xx se tratan como rechazo permanente; un `200` con
  `"error": true` en el body también cuenta como fallo.
- Payload plano en JSON. Evento principal: `order_payment` (también
  `link_paid` para links de pago). Próximamente: `order_created`,
  `order_confirmed`, `order_cancelled`, `order_refunded` (y para partners:
  `integration_installed`, `store_updated`, `store_deleted`).
- Usar `id_order` / `id_external` (el `order_key` enviado al crear la
  orden) para deduplicar.

**Verificación de firma (HMAC-SHA256):** header `X-Wava-Signature` con el
hash hexadecimal del body crudo usando el secreto del webhook. Comparar
siempre con una función de tiempo constante (`hmac.compare_digest` en
Python, `crypto.timingSafeEqual` en Node, `hash_equals` en PHP), nunca con
`==`.

```python
import hmac, hashlib

expected = hmac.new(
    secret.encode("utf-8"),
    payload_string.encode("utf-8"),
    hashlib.sha256,
).hexdigest()

hmac.compare_digest(expected, received_signature)
```

## 8. Links de pago

`POST /v1/links` (header `merchant-key`). Único campo obligatorio:
`description`. Si se omite `amount`, el comprador define el monto. Otros
campos: `currency`, `order_key`, `ttl_minutes` (1–525600), y los tres
`redirect_link*`.

```json
{
  "data": {
    "link": "https://checkout.wava.co/link/abc123def456",
    "hash": "abc123def456",
    "expires_at": "2026-06-18T14:30:00.000Z",
    "wallet_id": null
  }
}
```

El link lleva a un checkout hospedado por Wava que soporta Nequi, Daviplata,
Breb y Stripe.

## 9. Errores

Códigos agrupados por rango:

| Rango | Categoría |
|---|---|
| 1000–1099 | Autenticación (`1001` falta `merchant-key`, `1002` llave inválida, `1003`/`1004` permisos) |
| 2000–2099 | Validación (`2003` monto inválido, `2005` moneda inválida, `2006` email inválido, `2007` teléfono inválido…) |
| 3000–3099 | Orden / comercio (`3001` tienda no existe, `3003` orden no encontrada, `3018` reembolso vencido…) |
| 4000–4099 | Pago (`4002` procesamiento fallido, `4004` gateway no soportado…) |
| 5000–5099 | Servidor (`5002` no disponible, `5003` rate limit) |
| 6000+ | Específicos de cada pasarela (Nequi, Daviplata, etc.) |

## 10. Pruebas en sandbox

- **Nequi:** teléfono `+573001234567`; hacer `GET /v1/orders/{orderId}`
  auto-confirma la orden y dispara el webhook.
- **Daviplata:** OTP válidos `123456`, `000000`, `111111`; OTP inválido
  `999999` (error `DAVIPLATA_OTP_ERROR`, código `6105`).
- **Cédula de prueba:** cualquier cadena numérica, p. ej. `12345678`.

## 11. Checklist para salir a producción ("Go Live")

- Registro de negocio colombiano válido, y al menos una pasarela
  implementada.
- Pruebas de éxito, fallo y cancelación en sandbox para cada pasarela.
- Webhook de producción respondiendo `200 OK`.
- Manejo de errores/timeouts, uso de `order_key` para evitar duplicados.
- Todas las llamadas a la API deben hacerse desde el backend — nunca
  exponer el `merchant-key` en el cliente.
- Enviar a `go-live@wava.co`: nombre del negocio, URL, pasarelas
  implementadas, evidencia visual (capturas/video) del flujo completo y
  fecha de lanzamiento prevista. Revisión inicial: 2–3 días hábiles.

## 12. Recursos

- Documentación: https://docs.wava.co/
- Referencia de API / OpenAPI: https://docs.wava.co/api-reference/openapi.yaml
- Dashboard: https://app.wava.co (prod) / https://app.dev.wava.co (sandbox)
- Soporte: `soporte@wava.co`
- Integraciones sin código: WooCommerce, Tiendanube, Stripe

## 13. Notas para este proyecto

El sistema actual (`Sistema de gestión de incidencias`) es una aplicación
Flask de mesa de ayuda sin ningún flujo de cobro. Si en el futuro se decide
monetizar (p. ej. planes de soporte premium), esta guía resume lo necesario
para:

1. Registrar cuenta de desarrollador en https://app.dev.wava.co y obtener un
   `merchant-key` de sandbox.
2. Guardar el `merchant-key` como variable de entorno (siguiendo el patrón
   ya usado en `config.py` con `os.environ.get(...)`), nunca en el código.
3. Implementar un endpoint backend que llame a `POST /v1/orders` y un
   endpoint de webhook (`POST /webhooks/wava`) que verifique la firma
   HMAC antes de actualizar el estado del pago.
4. Completar el checklist de "Go Live" antes de usar credenciales de
   producción.
