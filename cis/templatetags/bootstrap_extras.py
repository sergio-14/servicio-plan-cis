# planificacion/templatetags/bootstrap_extras.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name="add_class")
def add_class(field, css):
    return field.as_widget(attrs={**field.field.widget.attrs, "class": f"{field.field.widget.attrs.get('class','')} {css}".strip()})

@register.filter(name="add_attrs")
def add_attrs(field, arg):
    """
    Uso: {{ form.campo|add_attrs:'placeholder=Buscar...,data-foo=bar' }}
    """
    attrs = {}
    for pair in arg.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            attrs[k.strip()] = v.strip()
    return field.as_widget(attrs={**field.field.widget.attrs, **attrs})

@register.simple_tag
def field_errors(field):
    if field.errors:
        return mark_safe('<div class="invalid-feedback d-block">{}</div>'.format(" ".join(field.errors)))
    return ""

@register.inclusion_tag("planificacion/_bs_field.html")
def render_bs_field(field, show_label=True):
    """
    Render rápido de un campo con label + input/select + help + errores (Bootstrap 5)
    """
    widget_class = "form-select" if field.field.widget.__class__.__name__ in ("Select", "SelectMultiple") else "form-control"
    # si ya tiene clase previa, la respetamos y agregamos
    prev_cls = field.field.widget.attrs.get("class", "")
    field.field.widget.attrs["class"] = f"{prev_cls} {widget_class}".strip()
    return {"field": field, "show_label": show_label}
