from django import template

register = template.Library()


@register.inclusion_tag("predictions/_cat_icon.html")
def cat_icon(value, size=28):
    try:
        tier = min(5, max(1, round(float(value))))
    except (TypeError, ValueError):
        tier = 3
    return {"tier": tier, "size": size}
