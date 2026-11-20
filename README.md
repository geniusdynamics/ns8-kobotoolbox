# ns8-kobotoolbox

Open source tool to design forms and collect data in the field, with offline collection and data export.

Module id: `kobotoolbox`. Images are pinned in `build-images.sh` and updated through reviewed changes.

## Install

```bash
add-module ghcr.io/geniusdynamics/kobotoolbox:latest 1
```

The command returns the instance id, for example `kobotoolbox1`. Use the id NS8 returns.

## Configure

```bash
api-cli run configure-module --agent module/kobotoolbox1 --data - <<'EOF'
{
  "host": "kobotoolbox.example.org",
  "http2https": true,
  "lets_encrypt": false
}
EOF
```

| Parameter | Required | Type | Description |
|---|---|---|---|
| `host` | yes | string | Host name for the application, like 'kobotoolbox.domain.org' |
| `lets_encrypt` | yes | boolean | Request a valid Let's Encrypt certificate. |
| `http2https` | yes | boolean | Redirect all the HTTP requests to HTTPS |

## OpenID Connect sign-in

In NS8 **Settings**, enable **OpenID Connect**. Choose **NS8 provider** and select an identity provider and user domain. NS8 registers the application and its callback. For an external provider, choose **Enter an external provider** and use **Advanced manual OIDC settings**.

For manual setup, enter the HTTPS issuer URL, client ID, client secret and optional sign-in button label. Save, then copy the callback URL shown in Settings to the provider. Use a confidential client with authorization code, S256 PKCE, and the `openid` scope. Keep the provider subject identifiers stable.

The NS8-managed provider appears alongside local password sign-in and providers added through Django admin. To link an existing KoboToolbox account, sign in to that account first and connect the provider from the account settings. Test the new sign-in in a separate browser session and keep a local administrator separate from SSO. Accounts that KoboToolbox makes SSO-only require their provider even though the site still offers password sign-in.

Leave the secret blank to keep it for the same issuer and client ID. Changing either creates a separate provider identity and requires a new secret and callback registration. Turning off the NS8 provider removes its sign-in option and preserves account links for the same issuer and client. Its settings are included in NS8 backups.

## Configuration output

`get-configuration` returns the hostname, TLS settings and OIDC configuration. The client secret is represented only by a configured flag.

## Images

| Image | Version |
|---|---|
| `docker.io/postgis/postgis` | `17-3.7` |
| `docker.io/valkey/valkey` | `9.1.3-alpine3.24` |
| `docker.io/mongo` | `8.0.38` |
| `docker.io/nginx` | `1.31.8-alpine3.24` |
| `docker.io/kobotoolbox/kpi` | `2.026.37g` |
| `docker.io/kobotoolbox/enketo-express-extra-widgets` | `7.6.5` |

The pod follows kobo-docker on a single host name: nginx (port 8080) serves KPI on
`/` and Enketo Express on `/enketo/`. The KoboCAT endpoints are served by KPI on the
same host. The `admin` password is in `state/secrets.env`.

## Network and access

- Reserves one TCP port on the node. The web application is published through Traefik on the configured host name.
- Runs rootless.
- Declares these NS8 authorizations: `traefik@node:routeadm`.

## Backup

The following paths are included in the NS8 backup (`imageroot/etc/state-include.conf`):

- `state/secrets.env`
- `state/kobotoolbox.pg_dump`, `state/kobocat.pg_dump`, `state/formhub.mongo_archive`
- `volumes/kpi-media`
- `volumes/kobocat-media`

## Services

- `enketo_express-app.service`
- `kobotoolbox.service`
- `kpi-app.service`
- `kpi_worker-app.service`
- `mongo-app.service`
- `nginx-app.service`
- `postgres-app.service`
- `redis-app.service`

## Get the configuration

```bash
api-cli run get-configuration --agent module/kobotoolbox1
```

## Update and uninstall

```bash
api-cli run update-module --data '{"module_url":"ghcr.io/geniusdynamics/kobotoolbox:latest","instances":["kobotoolbox1"],"force":true}'
remove-module --no-preserve kobotoolbox1
```

## Testing

Continuous integration:

- `Publish images` builds the module image on every push.
- `Test module` installs the image on a QEMU NS8 node and runs the Robot Framework suite in `tests/`. It runs after `Publish images` succeeds on `dev` and on `main`.
- `Build API JSON Schema docs` and the security scan run alongside.

The suite installs the module, configures a host name, checks that the web application answers through Traefik, takes UI screenshots and removes the module.

Run it locally with the NS8 standard infrastructure described in the [ns8-github-actions README](https://github.com/NethServer/ns8-github-actions/blob/v1/README.md#running-tests-locally).

## Upstream

Application documentation: https://support.kobotoolbox.org/

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
