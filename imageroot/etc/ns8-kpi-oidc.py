# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os

from allauth.socialaccount.models import SocialApp
from django.db import transaction

apps = json.loads(os.environ.get("KOBO_NS8_OIDC_APPS", "[]"))

with transaction.atomic():
    managed = SocialApp.objects.filter(provider="openid_connect", settings__ns8_managed=True)
    active_ids = []
    for data in apps:
        provider_id = data["provider_id"]
        if SocialApp.objects.filter(provider_id=provider_id).exclude(pk__in=managed).exists():
            raise RuntimeError("An existing KoboToolbox provider uses the NS8 provider ID")
        app, _ = managed.update_or_create(
            provider_id=provider_id,
            defaults={
                "provider": "openid_connect",
                "name": data["name"],
                "client_id": data["client_id"],
                "secret": data["secret"],
                "settings": {**data["settings"], "ns8_managed": True},
            },
        )
        active_ids.append(app.pk)
    # SocialAccount links use the provider ID and survive removal of a SocialApp.
    managed.exclude(pk__in=active_ids).delete()
