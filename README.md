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

## Configuration output

`get-configuration` returns: `host`, `lets_encrypt`, `http2https`.

## Images

| Image | Version |
|---|---|
| `docker.io/postgis/postgis` | `17-3.7` |
| `docker.io/valkey/valkey` | `9.2` |
| `docker.io/mongo` | `9.0.8` |
| `docker.io/nginx` | `1.31.8-alpine3.24` |
| `docker.io/kobotoolbox/kpi` | `2.026.37g` |
| `docker.io/kobotoolbox/enketo-express-extra-widgets` | `7.6.5` |

## Network and access

- Reserves 1 TCP port(s) on the node. The web application is published through Traefik on the configured host name.
- Runs rootless.
- Declares these NS8 authorizations: `traefik@node:routeadm`.

## Backup

The following paths are included in the NS8 backup (`imageroot/etc/state-include.conf`):

- `state/postgres.env`
- `volumes/./initdb.sql`
- `state/redis.env`
- `state/mongo.env`
- `state/nginx.env`
- `volumes/./nginx.conf`
- `volumes/./.vols/kobocat_media_uploads`
- `volumes/./.vols/kpi_media/__public`
- `state/kpi.env`
- `volumes/./kpi`
- `volumes/./.vols/kobocat_media_uploads`
- `state/kpi_worker.env`
- `volumes/./kpi`
- `state/enketo_express.env`

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

## Open items

Found by the NS8 module standards check. These must be resolved before a stable release:

- README still has the template boilerplate
- MARIADB_IMAGE is used by the module but no image in the label provides it: leftover from the template?

## Upstream

Application documentation: https://support.kobotoolbox.org/

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
