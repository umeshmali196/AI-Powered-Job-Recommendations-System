from django import template

from allauth.socialaccount.adapter import get_adapter


register = template.Library()


@register.simple_tag(takes_context=True)
def provider_enabled(context, provider):
    request = context.get('request')
    if request is None:
        return False
    return bool(get_adapter(request).list_apps(request, provider=provider))
