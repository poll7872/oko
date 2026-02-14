# OKO CLI

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-yellow)
![CLI](https://img.shields.io/badge/interface-CLI-lightgrey)
![Build](https://img.shields.io/badge/build-hatchling-blueviolet)

**OKO** es una CLI ligera para probar APIs y endpoints desde terminal.

Diseñada para flujo rápido: colecciones, aliases claros, variables, ejecución inmediata y salida legible.

---

## ¿Qué resuelve?

- Organizar endpoints por colección
- Reutilizar variables globales (`{{base_url}}`, `{{token}}`, etc.)
- Ejecutar requests con params, headers y body JSON
- Pedir variables faltantes de forma interactiva
- Reutilizar valores anteriores con defaults por historial
- Previsualizar requests sin enviarlas (`--dry-run`)

---

## Instalación

```bash
pip install oko-cli
```

## Inicio rápido

```bash
oko init
```

---

## Ejemplo completo (API ficticia)

Para documentar comandos de forma consistente, usaremos una API ficticia:

- Nombre: **Aurora Store API**
- Base URL: `https://api.aurora-store.test`
- Recurso principal: `products`

### 1) Crear colección

```bash
oko collection add catalog
oko collection list
```

### 2) Configurar variables globales

```bash
oko variable add base_url=https://api.aurora-store.test
oko variable add auth_token=demo-token-123
oko variable list
```

### 3) Registrar endpoints con aliases claros

```bash
# Listar productos
oko endpoint add catalog ProductsList '{{base_url}}/products' --method GET

# Buscar por categoría con paginación
oko endpoint add catalog ProductsByCategory '{{base_url}}/products?category={{category}}&take={{take}}&skip={{skip}}' --method GET

# Obtener detalle por id
oko endpoint add catalog ProductDetail '{{base_url}}/products/{{product_id}}' --method GET

# Crear producto
oko endpoint add catalog ProductCreate '{{base_url}}/products' --method POST

oko endpoint list catalog
```

### 4) Ejecutar endpoints

Ejecución directa:

```bash
oko endpoint run catalog ProductsList
```

Con variables runtime (forma larga):

```bash
oko endpoint run catalog ProductsByCategory \
  --var category=hoodies \
  --var take=10 \
  --var skip=0
```

Con variables runtime (forma compacta):

```bash
oko endpoint run catalog ProductsByCategory --vars category=hoodies,take=10,skip=0
```

Con headers:

```bash
oko endpoint run catalog ProductDetail \
  --var product_id=42 \
  -H Authorization='Bearer {{auth_token}}'
```

Con body JSON:

```bash
oko endpoint run catalog ProductCreate \
  --json '{"name":"Aurora Hoodie","price":49.9,"inventory":25}'
```

### 5) Prompt interactivo de variables faltantes

Si ejecutas un endpoint sin pasar todas las variables necesarias, OKO las solicita:

```bash
oko endpoint run catalog ProductsByCategory
```

Notas:

- Si ya usaste valores antes, aparecerán como **default** en el prompt.
- Presiona `Enter` para reutilizar el valor sugerido.

### 6) Validar sin enviar request (`--dry-run`)

```bash
oko endpoint run catalog ProductsByCategory --vars category=hoodies,take=5,skip=0 --dry-run
```

Muestra request final resuelta (método, URL, params, headers, JSON) sin hacer llamada HTTP.

### 7) Ejecución no interactiva

Útil para CI/scripts cuando quieres fallar si faltan variables:

```bash
oko endpoint run catalog ProductsByCategory --no-prompt-missing
```

---

## Sintaxis de variables

OKO resuelve variables en:

- URL
- Query params
- Headers
- JSON body

Ejemplos:

```text
{{base_url}}
{{auth_token}}
{{user.id}}
```

---

## Comandos de referencia rápida

```bash
oko init
oko collection add <name>
oko collection list
oko variable add <key>=<value>
oko variable list
oko variable delete <key>
oko endpoint add <collection> <alias> <url> --method <GET|POST|PUT|PATCH|DELETE>
oko endpoint list <collection>
oko endpoint run <collection> <alias> [opciones]
```

Opciones útiles de `endpoint run`:

- `--var key=value` (repetible)
- `--vars key1=v1,key2=v2`
- `-p key=value` (query param)
- `-H key=value` (header)
- `--json '{...}'`
- `--prompt-missing / --no-prompt-missing`
- `--dry-run`

---

## Filosofía

OKO es intencionalmente simple:

- Sin UI
- Sin cuentas
- Sin sincronización
- Sin dependencia de nube

Solo terminal, endpoints y foco.

---

## Requisitos

- Python 3.8+

## Estado

Proyecto en desarrollo activo.
