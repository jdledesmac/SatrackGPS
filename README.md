# SATRACK → QUADMinds Bridge (SapiQ.py)

**Overview**

- **Purpose:** A lightweight Python bridge that consumes location/events from the SATRACK GraphQL API, transforms them and forwards them to the QUADMinds API so fleet positions and events can be monitored in the Quadminds application.
- **Main script:** `SapiQ.py` (long-running polling loop)

**Features**

- Authenticate to SATRACK and fetch the latest events via GraphQL.
- Map and transform event fields to QUADMinds payload format.
- Post batched JSON to QUADMinds using an API key.
- Simple token refresh handling (re-login on 401 / ExpiredToken).
- Config-driven endpoints and credentials (via an external configuration file).

**Requirements**

- Python 3.8+
- Third-party package: `requests`


**Configuration (`.conf`)**

Place a configuration `.conf` file next to `SapiQ.py`. Example layout:

```ini
[s_endpoint]
url_token = https://source_api.example.com/oauth/token
url_loc   = https://source_api.example.com/graphql

[user_st]
client_id     = CLIENT_ID
client_secret = CLIENT_SECRET
grant_type    = client_credentials

[q_endpoint]
url_quad    = https://target_api.example.com/api/ingest
client_quad = YOUR_PROVIDER_NAME
q_key    = YOUR_TARGET_API_KEY
```

Notes:
- `url_token` is the SATRACK token endpoint (POST with client credentials).
- `url_loc` is the SATRACK GraphQL endpoint used to request `last(...)` events.
- `q_key` is the `x-saas-apikey` header value QUADMinds expects.

**How it works (high level)**

1. Read the configuration file `.conf` and build the credentials payload.
2. Obtain an OAuth access token using `login_satrack()`.
3. Enter a polling loop:
   - Query SATRACK GraphQL (`run_satrack_query()`), parse `data.last` events.
   - For each event, build a QUADMinds JSON item (fields: `id`, `event_id`, `reportDate`, `ignition`, `latitude`, `longitude`, `speed`, `course`, `holder_domain`, `temperature`).
   - Post payload to QUADMinds with `run_quad()`.
   - Sleep (60s by default) and repeat.
4. If SATRACK returns 401, an `ExpiredToken` is raised; bridge re-authenticates and resumes.

**Key implementation details**

- `query_loc` (in script) is a GraphQL query that requests: `unifiedEventCode, generationDateGMT, ignition, latitude, longitude, speed, direction, serviceCode, temperature`.
- `get_course(direction)` maps human-friendly direction words to numeric course degrees. Unknown values return `"Undefined direction"`.
- The QUADMinds payload is a dictionary with `provider` and `data` (list of events). Each item gets a generated `id` combining the script timestamp and a counter.
- Polling interval: change `time.sleep(60)` near the bottom of `SapiQ.py` to alter frequency.

**Example QUADMinds payload (one item)**

```json
{
  "provider": "YOUR_PROVIDER",
  "data": [
    {
      "id": "202511161230450",
      "event_id": 4,
      "reportDate": "2025-11-16T12:30:45Z",
      "ignition": true,
      "latitude": -34.6037,
      "longitude": -58.3816,
      "speed": 40,
      "course": 0,
      "holder_domain": "SERVICE_CODE",
      "temperature": 22.5
    }
  ]
}
```

**Running the bridge**

- Run under a process manager (systemd, Windows Task Scheduler, NSSM, or as a container) for production.
- The script prints a short startup message and then logs status messages to stdout.


**Logging & troubleshooting**

- The script prints brief status messages and errors to stdout.
- If you see unexpected responses, check:
  - `vars.conf` values (endpoints, keys)
  - network connectivity to SATRACK and QUADMinds
  - that the SATRACK credentials are valid and have rights to query `last(...)` events
- Common failure modes:
  - Missing or malformed `vars.conf` keys — the script prints `Check config file. Missing key:` and the missing key name.
  - HTTP 401 from SATRACK — the code attempts to re-authenticate.
  - QUADMinds returns non-`ok` status — the script prints the response content.

**Customization**

- Adjust `query_loc` if you need additional fields from SATRACK.
- Change the `get_course()` mapping if you need different degree values.
- Modify the `event_id` value assigned to events or add logic to translate `unifiedEventCode` to QUADMinds `event_id` values.
- If you prefer more robust logging, replace `print()` calls with the `logging` module and configure file or syslog handlers.

**Security**

- Keep `vars.conf` readable only by the service user. Do not commit secrets to source control.
- Consider using a secrets manager (Vault, AWS SSM, Azure Key Vault) in production instead of flat config files.

**Packaging & Deployment**

- This script is ready to run as a standalone Python process.
- For a Windows service use NSSM or a scheduled task; on Linux create a `systemd` service unit.
- Optionally bundle with PyInstaller if you want a single binary for target platforms (note the script already includes a helper `resource_path()` to support PyInstaller `_MEIPASS`).

**Extending / Next steps**

- Add retries with exponential backoff for HTTP POSTs to QUADMinds.
- Add structured logging and monitoring metrics (prometheus, health endpoints).
- Add unit tests for the transformation functions (`get_course`, payload construction).


