# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
import re
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

CONFIG = "oidc.json"
CALLBACK = ''


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


def resolve(request, apply=False):
    incoming = request.get("oidc")
    previous = load()
    if incoming is None and previous.get("enabled") and previous.get("mode") == "ns8":
        incoming = {"enabled": True, "mode": "ns8", "provider": previous["provider"],
                    "domain": previous["domain"], "confirmed": True}
    if incoming is None:
        config = previous
    elif not incoming["enabled"]:
        config = {**previous, "enabled": False}
    elif not request["http2https"]:
        invalid("oidc_mode", "oidc_https_required")
    elif incoming.get("mode") == "ns8":
        config = managed(request, incoming, previous, apply)
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
        same_client = previous.get("mode", "manual") == "manual" and (issuer, client_id) == (previous.get("issuer"), previous.get("client_id"))
        secret = incoming.get("client_secret") or (previous.get("client_secret") if same_client else "")
        if not secret:
            invalid("oidc_client_secret", "oidc_secret_required")
        config = {"enabled": True, "mode": "manual", "issuer": issuer, "client_id": client_id, "client_secret": secret}
        # Preserve the provider label for configuration edits.
        config["name"] = incoming.get("name", "").strip() or "OpenID Connect"
    return config


def providers():
    import agent
    from agent.ldapproxy import Ldapproxy

    rdb = agent.redis_connect(use_replica=True)
    records = agent.list_service_providers(rdb, "oidc", "http", sortby="module_seq_asc")
    if not records:
        return []
    domains = sorted(Ldapproxy().get_domains_list())
    result = []
    for record in records:
        module = record.get("module_id", "")
        uuid = record.get("module_uuid")
        prefix = record.get("issuer_url_prefix", "")
        host = record.get("host", "")
        if not uuid or not re.fullmatch(r"(?:idp|keycloak|lemonldapng)[0-9]+", module):
            continue
        try:
            if not host or urlsplit(prefix).netloc != host or not prefix.startswith(f"https://{host}/") or not prefix.endswith("/"):
                continue
        except ValueError:
            continue
        served_domains = [domain for domain in domains if not record.get("domain") or domain == record["domain"]]
        if served_domains:
            result.append({"id": uuid, "module": module, "label": record.get("ui_name") or module,
                           "prefix": prefix, "domains": served_domains})
    return result


def callback_path(config):
    return CALLBACK if CALLBACK else f"/accounts/oidc/{provider_id(config)}/login/callback/"


def managed(request, incoming, previous, apply):
    import agent
    import agent.tasks

    provider = incoming.get("provider", "")
    domain = incoming.get("domain", "")
    client_id = os.environ["MODULE_ID"]
    host = request["host"].lower()
    if (previous.get("enabled") and previous.get("mode") == "ns8"
            and previous.get("provider") == provider
            and previous.get("domain") == domain and previous.get("registered_host") == host
            and previous.get("client_id") == client_id and previous.get("client_secret")):
        return {**previous, "enabled": True}

    endpoint = next((p for p in providers() if p["id"] == provider), None)
    if not endpoint:
        invalid("oidc_provider", "oidc_provider_unavailable")
    if domain not in endpoint["domains"]:
        invalid("oidc_domain", "oidc_domain_unavailable")
    issuer = endpoint["prefix"] + domain
    result = {"enabled": True, "mode": "ns8", "provider": provider, "domain": domain,
              "issuer": issuer, "client_id": client_id, "registered_host": host,
              "name": endpoint["label"][:64]}
    if not apply:
        return result

    rdb = agent.redis_connect()
    bound = agent.get_bound_domain_list(rdb)
    added = domain not in bound
    if added and not agent.bind_user_domains([*bound, domain]):
        invalid("oidc_domain", "oidc_registration_failed")
    try:
        response = agent.tasks.run(
            f"module/{endpoint['module']}", "register-client",
            data={"domain": domain, "redirect_uris": [f"https://{host}{callback_path(result)}"],
                  "post_logout_redirect_uris": []},
            extra={"isNotificationHidden": True},
        )
        output = response.get("output")
        if (response.get("exit_code") != 0 or not isinstance(output, dict)
                or output.get("client_id") != client_id or output.get("issuer") != issuer
                or output.get("realm") != domain or not isinstance(output.get("client_secret"), str)
                or not output["client_secret"]):
            raise ValueError()
    except Exception:
        if added:
            agent.bind_user_domains(bound)
        invalid("oidc_provider", "oidc_registration_failed")
    result["client_secret"] = output["client_secret"]
    return result
