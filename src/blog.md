---
layout: default
title: Blog - IBS
permalink: /blog/
---

# 📝 Blog del IBS

Aquí encontrarás todas las publicaciones sobre el Índice de Bioactividad del Suelo.

<div class="blog-list">
{% for post in site.posts %}
<article class="blog-post">
    <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
    <p class="post-meta">
        <time datetime="{{ post.date | date_to_xmlschema }}">
            {{ post.date | date: "%d de %B de %Y" }}
        </time>
        {% if post.categories %}
            · Categorías: {{ post.categories | join: ", " }}
        {% endif %}
    </p>
    <p>{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
    <a href="{{ post.url | relative_url }}" class="btn">Leer más →</a>
</article>
{% endfor %}
</div>