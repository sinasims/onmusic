from .models import Setting, Advertisement


def site_settings(request):
    settings_dict = {}
    for s in Setting.objects.all():
        settings_dict[s.key] = s.value
    return {'site_config': settings_dict}


def ad_modal(request):
    ad = Advertisement.objects.filter(is_active=True).order_by('?').first()
    return {'site_ad': ad}
