---
layout: default
title: IBS - Índice de Bioactividad del Suelo
---

# 🌱 Índice de Bioactividad del Suelo (IBS)

**Marco abierto para la evaluación rápida de la actividad microbiana y la toma de decisiones agronómicas**

<div class="card">
## 📊 Estado del Proyecto

- **Versión:** v0.0.1-beta
- **Última actualización:** Junio 2026
- **Licencia:** MIT
- **Tecnologías:** 
  - Python 38.7%
  - HTML 33.2%
  - PHP 18.7%
  - Ruby 9.4%

<a href="https://github.com/stndcx/ibs" class="btn">📂 Ver código en GitHub</a>
</div>

<div class="card">
## 🚀 ¿Qué es el IBS?

El **Índice de Bioactividad del Suelo (IBS)** es una herramienta de código abierto diseñada para:

- Evaluar rápidamente la actividad microbiana del suelo
- Ayudar en la toma de decisiones agronómicas
- Proporcionar un marco estandarizado para el análisis

Este proyecto está en desarrollo activo y busca ser un recurso útil para la comunidad agrícola y científica.
</div>

<div class="card">
## 📝 Últimas Publicaciones

{% for post in site.posts limit:3 %}
- [{{ post.title }}]({{ post.url | relative_url }}) - {{ post.date | date: "%d/%m/%Y" }}
{% endfor %}

{% if site.posts.size == 0 %}
*No hay publicaciones aún. ¡Sé el primero en escribir un post!*
{% endif %}
</div>

## 🔧 ¿Cómo contribuir?

1. Haz un fork del repositorio
2. Crea una rama para tu contribución
3. Envía un pull request

¡Toda ayuda es bienvenida!