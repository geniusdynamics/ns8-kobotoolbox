# SPDX-License-Identifier: GPL-3.0-or-later
from .prod import *

import json as _json
import os as _os

_ns8_apps = _json.loads(_os.environ.get("KOBO_NS8_OIDC_APPS", "[]"))
if _ns8_apps:
    SOCIALACCOUNT_PROVIDERS = dict(globals().get("SOCIALACCOUNT_PROVIDERS", {}))
    _oidc = SOCIALACCOUNT_PROVIDERS.setdefault("openid_connect", {})
    _oidc["APPS"] = [*_oidc.get("APPS", []), *_ns8_apps]
