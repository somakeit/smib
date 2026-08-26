# Space Open Probability — Heatmap Chart

A Grafana panel showing the probability that the space is open, broken down by day of week and time of day, as a 7×N heatmap. Rendered via the [ECharts panel](https://volkovlabs.io/plugins/business-charts/) plugin, sourced through the [Infinity datasource](https://sriramajeyam.com/grafana-infinity-datasource/).

This chart pulls directly from the `weekly-bucket` endpoint added in [somakeit/smib#540](https://github.com/somakeit/smib/pull/540), which exposes bucketed space-open metrics as JSON for Grafana. It has no dependency on a separate metrics store — point the Infinity datasource straight at your SMIB instance.

## Files

| File        | Purpose                                                                                                                                                                                                                                        |
|-------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `chart.js`  | The `visualEditor.code` function — builds the ECharts `option` object (heatmap + responsive breakpoints) from the query response. Paste this into the panel's **ECharts editor → Code** tab, or reference it when regenerating the panel JSON. |
| `README.md` | This file.                                                                                                                                                                                                                                     |

The panel is provisioned as part of the dashboard JSON at `dashboards/space-open-probability.json` in the Grafana provisioning setup — this directory holds the chart source separately so it's easier to diff and edit outside the panel JSON blob.

## How it works

1. **Query.** The Infinity datasource makes a `GET` request against `/api/metrics/spacestate/weekly-bucket`, passing three params derived from the Grafana time picker:

   | Param            | Value                       | Description                                                                                                                  |
      |------------------|-----------------------------|------------------------------------------------------------------------------------------------------------------------------|
   | `start`          | `${__from:date:YYYY-MM-DD}` | Start of the accumulation period (optional — omitting it lets the API pick its own default)                                  |
   | `end`            | `${__to:date:YYYY-MM-DD}`   | End of the accumulation period (optional, same as above)                                                                     |
   | `bucket_minutes` | `60`                        | Bucket size in minutes — **only `15`, `30`, or `60` are accepted**; anything else gets a `422`. Defaults to `30` if omitted. |

2. **Expected response shape.** `chart.js` reads `context.panel.data.series[0].meta.custom.data`. Verified against the live OpenAPI schema (SMIB v2.3.0) at `/openapi.json`:

   ```json
   {
     "metadata": {
       "requested_start": "2026-08-01",
       "requested_end": "2026-08-26",
       "first_event_timestamp": "2026-08-01T08:03:12Z",
       "last_event_timestamp": "2026-08-26T21:47:05Z",
       "bucket_minutes": 60,
       "total_events_processed": 1234
     },
     "buckets": [
       {
         "weekday_index": 0,
         "time_index": 540,
         "bucket_minutes": 60,
         "open_seconds": 1500,
         "total_bucket_seconds": 3600,
         "weekday": "monday",
         "time": "09:00",
         "open_minutes": 25,
         "open_ratio": 0.42
       }
     ]
   }
   ```

    - `weekday_index`: `0` = Monday … `6` = Sunday (`weekday`/`time` are read-only human-readable labels for the same data — `chart.js` doesn't use them, it derives its own labels from `weekday_index`/`time_index`)
    - `time_index`: minutes since midnight, `0`–`1439` (e.g. `540` = 09:00)
    - `open_ratio`: fraction of the bucket the space was open, `0`–`1`
    - `total_events_processed`: if `0` or absent, the chart renders an empty-state message instead of the heatmap

3. **Colour scaling.** Raw `open_ratio` values are **not** plotted linearly — the script computes the median non-zero ratio and rescales around it (values below the median compress into the bottom 35% of the colour range, values above stretch across the top 65%). This keeps a handful of very-high outlier buckets from washing out the rest of the heatmap. Buckets under 10% raw are floored to 0.
4. **"Now" marker.** A red `markLine` is drawn at the current day/time so you can see at a glance where "now" sits against the historical pattern.
5. **Responsiveness.** Three `media` breakpoints (`maxWidth: 720`, `maxWidth: 480`, `maxHeight: 300`) shrink fonts, hide the y-axis tick labels, and swap in a scrollable `dataZoom` slider on the x-axis for narrow/embedded views — relevant for the public-dashboard embed use case.

## Manual installation

These steps set the panel up by hand through the Grafana UI — no dashboard-provisioning files required. If you don't have Grafana running yet, see the [official installation docs](https://grafana.com/docs/grafana/latest/setup-grafana/installation/) first.

**Prerequisites**
- A running SMIB instance with [PR #540](https://github.com/somakeit/smib/pull/540) merged (it's on `master`), reachable from your Grafana host.
- The endpoint and schema below are confirmed against a live `/openapi.json` (SMIB v2.3.0) — if you're running a different version, sanity-check your own instance's `https://<your-smib-host>/api/docs` (Swagger UI) or `/openapi.json` first, since query params/schema could shift between versions.

### 1. Install the required plugins

- [`volkovlabs-echarts-panel`](https://grafana.com/grafana/plugins/volkovlabs-echarts-panel/) (Business Charts)
- [`yesoreyeram-infinity-datasource`](https://grafana.com/grafana/plugins/yesoreyeram-infinity-datasource/) (Infinity)

Use whichever install method fits your setup (UI plugin catalogue, `grafana-cli`, or the `GF_INSTALL_PLUGINS` environment variable) — see Grafana's [plugin management docs](https://grafana.com/docs/grafana/latest/administration/plugin-management/). Restart Grafana afterwards.

### 2. Add the Infinity datasource

- **Connections → Data sources → Add new data source → Infinity**.
- No credentials are required for this endpoint. Optionally restrict allowed URLs to your SMIB host under **URL, params & headers** if you want to lock the datasource down.
- **Save & test**.
- See the [Infinity datasource docs](https://sriramajeyam.com/grafana-infinity-datasource/) or Grafana's general [datasource docs](https://grafana.com/docs/grafana/latest/datasources/) for more.

### 3. Build the panel

On a dashboard, **Add → Visualisation**, pick the Infinity datasource, and configure the query:

| Setting    | Value                                                                                                                                  |
|------------|----------------------------------------------------------------------------------------------------------------------------------------|
| Type       | JSON                                                                                                                                   |
| Parser     | Backend *(runs the request server-side — avoids browser CORS issues against your SMIB host)*                                           |
| Source     | URL                                                                                                                                    |
| Format     | Table                                                                                                                                  |
| URL        | `https://<your-smib-host>/api/metrics/spacestate/weekly-bucket`                                                                        |
| Method     | GET                                                                                                                                    |
| URL params | `start` = `${__from:date:YYYY-MM-DD}`, `end` = `${__to:date:YYYY-MM-DD}`, `bucket_minutes` = `60` (only `15`, `30`, or `60` are valid) |

Then:
- Change the panel's **Visualisation** type to **Business Charts**.
- In panel options, set **Editor → Visual**, and paste the contents of `chart.js` (this directory) into the code editor.
- Title the panel "Space Open Probability" and **Save dashboard**.

### 4. (Optional) Public embedding

See the main Grafana setup notes in this repo for enabling `Share → Public dashboard` and the `allow_embedding` config needed for iframe use.

## Grafana wiring

- **Panel type:** `volkovlabs-echarts-panel`
- **Datasource:** `yesoreyeram-infinity-datasource`. If provisioning from a dashboard JSON export instead of the manual steps above, the datasource UID must be pinned (e.g. `bft7ovhf49tz4c`) in both the datasource config and the panel JSON so the reference resolves.
- **Editor mode:** `visual` (uses `visualEditor.code`, not the legacy single-series `getOption` fallback — that field is unused dead weight from an older plugin version and can be ignored/removed).

## Updating the chart

Edit `chart.js`, then either:
- paste the updated code into the panel's ECharts code editor in the Grafana UI and re-export the dashboard JSON, or
- manually update the `visualEditor.code` string in `dashboards/space-open-probability.json` to match.

## Public embedding

This panel is designed to work standalone via Grafana's **Share → Public dashboard** feature (see the main Grafana provisioning docs in this repo). The responsive breakpoints above assume it may be embedded in an `<iframe>` at widths well below a typical desktop dashboard panel.