---
layout: default
title: Blog - IBS
permalink: /blog/
---

<div class="blog-list">
  <h1 style="font-family: var(--f-display); color: var(--tierra); font-size: 2.4rem; margin-bottom: 2rem;">Blog del IBS</h1>

  {% if site.posts.size == 0 %}
    <p style="color: var(--grafito);">Todavía no hay publicaciones. ¡La primera está por llegar!</p>
  {% else %}
    {% for post in site.posts %}
      <article class="blog-post">
        <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
        <p class="post-meta">
          <time datetime="{{ post.date | date_to_xmlschema }}">
            {{ post.date | date: "%d de %B de %Y" }}
          </time>
          {% if post.categories %}
            · {{ post.categories | join: ", " }}
          {% endif %}
        </p>
        <div class="post-excerpt">
          {{ post.excerpt | strip_html | truncatewords: 25 }}
        </div>
        <a href="{{ post.url | relative_url }}" class="btn">Leer más →</a>
      </article>
    {% endfor %}
  {% endif %}
</div>