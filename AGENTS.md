---
description: Contexto global del proyecto Fondo Capital
mode: coordinator
model: gpt-5.2-codex
temperature: 0.2
tools:
  allow:
    - read
    - glob
    - grep
    - bash
    - apply_patch
    - write
    - question
    - task
  deny:
    - webfetch
---

# Fondo Capital - Contexto Global

Proyecto Django con arquitectura por apps dentro de `applications/`. Entorno actual local con Docker Compose, PostgreSQL/PostGIS y Redis. El sistema maneja roles de gestor (staff) y usuario normal; la UI expone panel de gestor y panel de usuario.

Prioridades del proyecto:
- Orden y claridad del codigo por encima de la velocidad.
- Seguridad y control de acceso en todas las vistas y acciones.
- Cambios pequenos, mantenibles y faciles de revisar.
- Preparar una base limpia y estable para una futura puesta en produccion.

Reglas globales:
- Evitar mezclar logica de negocio en templates.
- Mantener consistencia entre roles (gestor vs usuario) en permisos y flujos.
- Cambios deben ser locales y sin efectos colaterales no deseados.
- Preferir soluciones simples y explicables.
