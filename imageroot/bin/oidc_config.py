# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

CONFIG = "oidc.json"


def load():
    try:
        return json.loads(Path(CONFIG).read_text())
    except FileNotFoundError:
        return {}


def write(name, content):
    with NamedTemporaryFile(mode="w", dir=".", prefix=".oidc-", delete=False) as target:
        temp_name = target.name
        try:
            target.write(content)
            target.close()
            os.replace(temp_name, name)
        finally:
            Path(temp_name).unlink(missing_ok=True)


def provider_id(config):
    # A different issuer or client can assign a different meaning to a subject.
    from hashlib import sha256

    identity = json.dumps([config["issuer"], config["client_id"]]).encode()
    return "ns8-" + sha256(identity).hexdigest()[:32]


def invalid(field, error):
    import agent

    agent.set_status("validation-failed")
    json.dump([{"field": field, "parameter": field, "error": error}], sys.stdout)
    sys.exit(3)


def resolve(request):
    incoming = request.get("oidc")
    previous = load()
    if incoming is None:
        config = previous
    elif not incoming["enabled"]:
        config = {**previous, "enabled": False}
    else:
        issuer = incoming.get("issuer", "")
        try:
            url = urlsplit(issuer)
            valid_issuer = (
                url.scheme == "https" and url.hostname and url.username is None
                and url.password is None and not url.query and not url.fragment
                and "?" not in issuer and "#" not in issuer and not any(c.isspace() for c in issuer)
                and "\\" not in issuer and (url.port is None or 0 < url.port <= 65535)
            )
        except ValueError:
            valid_issuer = False
        if not valid_issuer:
            invalid("oidc_issuer", "oidc_issuer_invalid")
        client_id = incoming.get("client_id", "").strip()
        if not client_id:
            invalid("oidc_client_id", "oidc_client_id_required")
        same_client = (issuer, client_id) == (previous.get("issuer"), previous.get("client_id"))
        secret = incoming.get("client_secret") or (previous.get("client_secret") if same_client else "")
        if not secret:
            invalid("oidc_client_secret", "oidc_secret_required")
        if not request["http2https"]:
            invalid("oidc_issuer", "oidc_https_required")
        config = {"enabled": True, "issuer": issuer, "client_id": client_id, "client_secret": secret}
        # Preserve the provider label for configuration edits.
        config["name"] = incoming.get("name", "").strip() or "OpenID Connect"
    return config
