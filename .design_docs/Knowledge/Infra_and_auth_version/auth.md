# Enterprise Engineering Manual: Architectural Blueprint for Databricks Apps with Flask

## 1. Executive Summary & Dual-Identity Architecture

In high-compliance enterprise environments, the strategic deployment of data applications requires a sophisticated balance between system autonomy and granular user governance. Databricks Apps implements this through a dual-identity architecture. This model allows applications to function as autonomous entities for operational tasks while strictly inheriting the identity and Unity Catalog (UC) permissions of the end-user for data-plane interactions. Architecting with this separation ensures that applications are "secure by design," preventing unauthorized privilege escalation while providing the transparency required for regulatory auditing.

### Analytical Comparison: App Authorization vs. User Authorization


|                       |                                                        |                                                               |
| --------------------- | ------------------------------------------------------ | ------------------------------------------------------------- |
| Feature               | App Authorization (M2M)                                | User Authorization (U2M / On-Behalf-Of)                       |
| **Identity Entity**   | Managed Service Principal (Unique UUID)                | Synchronized End-User                                         |
| **Use Cases**         | Background maintenance, system logging, usage metrics. | Dynamic querying, Genie AI agents, UC Volume access.          |
| **Governance Impact** | Static permissions granted to the App SP.              | Inherits row-level filters and column masks from UC policies. |
| **Lifecycle**         | Created at deployment; deleted at app removal.         | Bound to the active user session; relies on OAuth tokens.     |
| **Standard Protocol** | Machine-to-Machine (M2M)                               | User-to-Machine (U2M) / PKCE                                  |


### Architectural Justification

The coexistence of both identities is an architectural requirement for production integrity. The service principal identity maintains system-level state and telemetry—facilitating ingestion into OpenTelemetry (OTel) tables billed under the **Jobs Serverless SKU**—while the user identity ensures that no application logic can bypass data security boundaries. This dual-track approach ensures every data interaction is attributable to a specific human actor, fulfilling the core requirements of enterprise identity governance.

This logic is implemented through the physical network mechanics of the serverless compute plane and the Databricks L7 reverse proxy.

## 2. Ingress Topology & Header Mechanics

The security posture of a Databricks App is enforced at the edge. Databricks utilizes a managed Layer 7 reverse proxy to isolate the serverless execution environment, offloading the overhead of TLS termination and session management from the application layer.

### The Request Lifecycle

Requests follow a strict four-step traversal to reach the container:

1. **TLS 1.3 Termination:** The proxy terminates external secure connections using TLS 1.3. Custom TLS handling within the application is strictly forbidden.
2. **Contextual Session Verification:** The proxy validates workspace login tokens. If a session is absent, the proxy initiates an OAuth challenge (SSO or OTP).
3. **Direct Serverless Forwarding:** Validated traffic bypasses the control plane for low-latency routing directly to the serverless compute plane.
4. **H2C Proxying:** Traffic is forwarded to the application container via HTTP/2 Cleartext (H2C). Applications **must** bind to `0.0.0.0` and listen on the port defined by the `DATABRICKS_APP_PORT` environment variable.

### PrivateLink and DNS Configuration

For maximum isolation, ingress must be routed via AWS PrivateLink. This requires the registration of a VPC interface endpoint to the regional General Access service. To prevent DNS resolution to public IPs, a Route 53 Private Hosted Zone (PHZ) must be configured for `privatelink.cloud.databricks.com` with the following A-record targets:

- `*.databricksapps.com` (Standard) -> Private IP of the General Access VPC Endpoint.
- `dbc-<workspace-id>.cloud.databricks.com` -> VPC Interface Endpoint ID.

### Strategic Header Analysis

The proxy injects critical headers for application-level governance:

- `x-forwarded-access-token`: Contains the active user’s OAuth token, enabling "on-behalf-of" operations.
- `__Host-databricks-app-router`: A cookie used for session affinity. This ensures requests are routed to the same container instance, facilitating efficient local in-memory caching.

These headers allow the application layer to capture and propagate user context for governed data operations.

## 3. Secure Token Extraction & Management in Python

Horizontal scalability and security mandate stateless token handling. Caching credentials or persisting them in insecure environments is a critical failure point in cloud-native security.

### Implementation Patterns

Extract the user token directly from the request context using Flask’s header utility:

```python
from flask import request

def get_active_user_context():
    # Extract the user's OAuth token for Unity Catalog-scoped operations
    return request.headers.get('x-forwarded-access-token')

```

### Non-Negotiable Security Rules

Engineers must strictly adhere to the following security constraints:

- **Personal Access Tokens (PATs) are NOT supported:** Databricks Apps exclusively utilize OAuth credentials.
- **Forbidden: Caching tokens in server-side session cookies.** This risks exposure and technical debt; tokens must be treated as ephemeral.
- **Forbidden: Token exposure in** `stdout` **or** `stderr`**.** All logging logic must be audited to prevent credential leakage into OTel tables.
- **Forbidden: Hardcoding Secrets.** All credentials must be managed via the `valueFrom` manifest syntax using Databricks Secrets.

These tokens are the primary mechanism for establishing secure, per-user connections within a unified application blueprint.

## 4. The Enterprise-Grade Flask Blueprint

Production applications **must** utilize `uv` for dependency management to ensure reproducible builds via `uv.lock`. The container runtime executes as a **non-privileged user**, and system-level installations (e.g., `apt-get`) are blocked; all dependencies must be resolved at the language level.

### Core Application Code

```python
import os
import signal
import psycopg
from flask import Flask, request, jsonify
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config

app = Flask(__name__)

# 1. INITIALIZATION: Unified WorkspaceClient using SP Identity
# Environment variables DATABRICKS_CLIENT_ID and CLIENT_SECRET are auto-injected.
app_client = WorkspaceClient()

# 2. LAKEBASE PERSISTENCE: Custom Connection with Token Rotation
class OAuthConnection(psycopg.Connection):
    @classmethod
    def connect(cls, **kwargs):
        # PGUSER is automatically mapped to the SP Client ID
        # Lakebase schema: {app-name}_schema_{service-principal-id} (hyphens removed)
        cfg = Config()
        kwargs['password'] = cfg.authenticate() # SP exchanges ID for 1-hour token
        return super().connect(**kwargs)

# 3. USER-SCOPED DATA EXECUTION
@app.route('/api/query', methods=['POST'])
def query_on_behalf_of():
    user_token = request.headers.get('x-forwarded-access-token')
    if not user_token:
        return jsonify({"error": "Missing user context"}), 401

    sql_query = request.json.get('query')
    # Use user_token to connect to SQL Warehouse. 
    # UC row-level filters/column masks apply automatically.
    try:
        from databricks.sdk.service.sql import StatementExecutionAPI
        # Parameterized execution is an absolute requirement for security
        # Use workspace client with user-token for on-behalf-of flow
        user_client = WorkspaceClient(token=user_token)
        response = user_client.statement_execution.execute_statement(
            warehouse_id=os.getenv("SQL_WAREHOUSE_ID"),
            catalog="main",
            schema="default",
            statement=sql_query
        )
        return jsonify(response.as_dict())
    except Exception as e:
        return jsonify({"error": "Governance restriction or query error"}), 500

# 4. SYSTEM INTEGRITY: SIGTERM Handler
def handle_graceful_shutdown(signum, frame):
    # Runtimes have a strict 15-second window before SIGKILL
    print("SIGTERM received. Persisting state and closing connections...")
    exit(0)

signal.signal(signal.SIGTERM, handle_graceful_shutdown)

if __name__ == '__main__':
    port = int(os.getenv('DATABRICKS_APP_PORT', 8080))
    app.run(host='0.0.0.0', port=port)

```

Packaging this blueprint requires declarative manifests to bind identities and resources.

## 5. Declarative Bundles & Secure Resource Mapping

Databricks Asset Bundles (DABs) are the mandatory standard for ensuring environment parity. DABs explicitly bind the two identities by declaring scopes in the same manifest that manages the app's service principal permissions.

### Configuration Templates

#### `app.yaml`

```yaml
env:
  - name: SQL_WAREHOUSE_ID
    valueFrom: sql-warehouse # Key mapped in DAB or UI
  - name: GENIE_SPACE_ID
    valueFrom: genie-space

```

#### `databricks.yml`

```yaml
resources:
  apps:
    enterprise_flask_app:
      name: "prod-data-explorer"
      source_code_path: ./src
      command: ["uv", "run", "start-app"]
      user_api_scopes:
        - sql
        - genie
        - files
        - iam.access-control:read

```

### Scope Evaluation: The "So What?"

- `sql`: Authorizes query execution on SQL Warehouses. Without this, user tokens cannot access UC-managed data.
- `genie`: Enables the app to leverage conversational analytics on behalf of the user.
- `files`: Permits interaction with UC Volumes and workspace directories.
- `iam.access-control:read`: Mandatory for retrieving the active user's identity profile.

## 6. Production Security & Compliance Checklist

Before promotion to production, every application must undergo an automated security audit and telemetry verification.

### Compliance Checklist

- [ ] **Restricted Folder Permissions:** Source code must reside in folders restricted to the app owner.
- [ ] **Least-Privilege SP Scoping:** Verify the service principal only has `CAN USE` permissions on target resources.
- [ ] **Outbound Egress Hard Limits:** Ensure the network policy respects the following platform constraints:
  - Maximum of **2,500 total destinations**.
  - Limit of **100 allowed storage locations** (e.g., S3/GCS).
  - Limit of **100 allowed FQDN domains** (e.g., `pypi.org`).
- [ ] **Predictive Optimization:** Enable predictive optimization on target OTel Delta tables to ensure efficient query performance for logs.

### Observability & Billing

Telemetry flows via the Zerobus Ingest connector into Unity Catalog Delta tables:

- `otel_logs`: Capture of `stdout`/`stderr`.
- `otel_spans`: Distributed tracing metadata.
- `otel_metrics`: Resource utilization data.
- **Billing Awareness:** All telemetry ingestion is charged against the **Jobs Serverless SKU** and billed under **Lakeflow Connect**.

### Audit Record Design

Every user interaction must generate a structured audit record. These records should include the user's UUID, the action performed, and the target resource. This ensures that even in complex dual-identity flows, every state change is attributable, transparent, and compliant with modern enterprise security standards.