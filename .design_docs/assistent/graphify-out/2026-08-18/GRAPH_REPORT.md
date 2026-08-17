# Graph Report - D:/Work/Etex/Procure_AI_Workspace  (2026-08-18)

## Corpus Check
- 114 files · ~79,123 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1096 nodes · 2167 edges · 63 communities (38 shown, 25 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 342 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Chat Model Wrapper (LangChain)
- force-graph Library
- force-graph Rendering
- Model Catalog Registry
- You.com Search API
- marked.js Markdown Parser
- Auth Bridge & Gateway Credentials
- Global Logger Control Panel
- Flask & SQLAlchemy Core
- Identity & User Verification
- Agent Logger Wrapper
- force-graph Utilities
- Databricks Auth Providers
- Environment Config Reader
- Connector Hub
- force-graph Internals
- FastAPI Auth Dependencies
- OpenCode MCP Config
- force-graph Layout
- marked.js Tokens
- Connector Exceptions
- Document Text Service
- Builder Chat UI
- Profile Page UI
- CLI Token Cache
- New Project Form UI
- Usage Dedup Patch
- HTTPX Auth Client
- Log Redaction Filters
- Dashboard Home UI
- Logger Namespace Registry
- marked.js Helpers
- Client Logger JS
- API Fetch Wrapper JS
- Theme Toggle JS
- force-graph Canvas
- Profile Normalize Tests
- Graph Explorer UI
- Auth Shim (Legacy)
- Core Security Init
- Exceptions Shim (Legacy)
- Identity Shim (Legacy)
- Databricks Connectors Init
- Framework Integrations Init
- Connectors Utils Init
- Log Formatters
- Model Factory Init
- Model Factory Tests Init
- API Utilities Init
- Document Utils Init
- Shared Utilities Init
- Draggable Panel JS
- KG Build Dialog JS
- Chat Panel JS
- Evidence Panel JS
- Excel Renderer JS
- Preview Panel JS
- Sources Panel JS
- Studio Panel JS
- Panel Resizer JS
- Project Metadata

## God Nodes (most connected - your core abstractions)
1. `qa` - 50 edges
2. `n()` - 35 edges
3. `e()` - 35 edges
4. `EnvironmentConfig` - 28 edges
5. `qr()` - 26 edges
6. `ConnectorHub` - 25 edges
7. `r()` - 25 edges
8. `AuthProvider` - 24 edges
9. `AuthError` - 23 edges
10. `IdentityManager` - 22 edges

## Surprising Connections (you probably didn't know these)
- `test_resolver_refuses_embedding_override()` --calls--> `ModelFactoryResolver`  [INFERRED]
  shared_library/model_factory/tests/test_family_adapter.py → shared_library/model_factory/resolver.py
- `paragraph()` --indirect_call--> `n()`  [INFERRED]
  web_app/static/vendor/marked.min.js → web_app/static/vendor/force-graph.min.js
- `DatabricksHttpxAuth` --uses--> `EnvironmentConfig`  [INFERRED]
  shared_library/databricks_connectors/core/auth.py → shared_library/databricks_connectors/utils/env_reader.py
- `DatabricksHttpxAuth` --uses--> `AuthError`  [INFERRED]
  shared_library/databricks_connectors/core/auth.py → shared_library/databricks_connectors/utils/exceptions.py
- `AuthProvider` --uses--> `EnvironmentConfig`  [INFERRED]
  shared_library/databricks_connectors/core/auth.py → shared_library/databricks_connectors/utils/env_reader.py

## Import Cycles
- None detected.

## Communities (63 total, 25 thin omitted)

### Community 0 - "Chat Model Wrapper (LangChain)"
Cohesion: 0.05
Nodes (57): AsyncCallbackManagerForLLMRun, ChatGenerationChunk, HumanMessage, Runnable, RunnableConfig, _adapt(), _coerce_to_messages(), ConstraintAwareBoundRunnable (+49 more)

### Community 1 - "force-graph Library"
Cohesion: 0.03
Nodes (36): an(), ao(), Ba(), cn(), de(), displayable(), ee(), fo() (+28 more)

### Community 2 - "force-graph Rendering"
Cohesion: 0.05
Nodes (13): bi(), ci(), fi(), ge(), Hr(), na(), qa, qe() (+5 more)

### Community 3 - "Model Catalog Registry"
Cohesion: 0.07
Nodes (60): _badges_for(), _chat_eligible(), get_model_catalog(), _humanize(), _is_embedding(), list_models(), list_profiles(), _normalize_surface() (+52 more)

### Community 4 - "You.com Search API"
Cohesion: 0.06
Nodes (43): clamp_count(), extract_urls_from_text(), normalize_freshness(), parse_hit(), _passages_from_raw_hit(), Any, BaseException, Response (+35 more)

### Community 5 - "marked.js Markdown Parser"
Cohesion: 0.06
Nodes (42): A(), blockTokens(), br(), checkbox(), code(), codespan(), de(), del() (+34 more)

### Community 6 - "Auth Bridge & Gateway Credentials"
Cohesion: 0.07
Nodes (35): PromptInput, _extract_bearer_token(), GatewayCredentials, Auth bridge: Databricks WorkspaceClient credentials for AI Gateway calls. Never…, Bearer token + optional workspace host for OpenAI-compatible clients., Parse ``Authorization: Bearer <token>`` (case-insensitive)., Resolve AI Gateway API key from Databricks auth (no env mutation). Preference…, resolve_gateway_credentials() (+27 more)

### Community 7 - "Global Logger Control Panel"
Cohesion: 0.05
Nodes (43): Logger, RotatingFileHandler, bootstrap(), Central logging control panel - single source of truth for all logging…, Initialize Loguru, the stdlib→Loguru bridge, and log file handlers. This…, InterceptHandler, make_console_handler(), make_file_handler() (+35 more)

### Community 8 - "Flask & SQLAlchemy Core"
Cohesion: 0.11
Nodes (30): Base, datetime, Engine, Flask, scoped_session, Session, get_current_user(), _asset_data() (+22 more)

### Community 9 - "Identity & User Verification"
Cohesion: 0.10
Nodes (22): ConciergeContext, _display_from_groups(), get_verified_user_from_headers(), IdentityManager, _is_service_principal(), Any, WorkspaceClient, Identity translation, Full Metadata verification, and Concierge handoff. (+14 more)

### Community 10 - "Agent Logger Wrapper"
Cohesion: 0.07
Nodes (35): Agent system logger wrapper - Loguru-based with LangChain integration.…, agent_span(), catch(), get_logger(), _log_exception(), Any, BaseException, Agent logger wrapper implementation - Loguru-based with LangChain-aware… (+27 more)

### Community 11 - "force-graph Utilities"
Cohesion: 0.13
Nodes (31): a(), ae(), bo(), c(), co(), eu(), H(), i() (+23 more)

### Community 12 - "Databricks Auth Providers"
Cohesion: 0.10
Nodes (19): Config, AuthProvider, configure_connection_pooling(), AccountClient, Any, WorkspaceClient, Production authentication layer — UCA, httpx middleware, OIDC timeout hardening., Build an isolated ``Config`` without mutating ``os.environ``. (+11 more)

### Community 13 - "Environment Config Reader"
Cohesion: 0.12
Nodes (13): EnvironmentConfig, Any, Path, Environment configuration reader for the Databricks connector. Reads…, Priority: process env (DATABRICKS_* / upper) > YAML databricks/root > default., Local/dev/test tiers (CLI profile / U2M)., Process hub pool size (OBO clients use a smaller isolated pool of 10)., Build isolated SDK ``Config`` kwargs (no os.environ mutation). (+5 more)

### Community 14 - "Connector Hub"
Cohesion: 0.09
Nodes (17): ConnectorHub, get_current_identity(), get_hub(), hub_identity_ready(), AccountClient, Any, WorkspaceClient, Enterprise ConnectorHub — hybrid SDK delegation + typo-safe ``.rest()``. (+9 more)

### Community 15 - "force-graph Internals"
Cohesion: 0.13
Nodes (25): ai(), e(), eo(), fe(), he(), io(), jo(), Ka() (+17 more)

### Community 16 - "FastAPI Auth Dependencies"
Cohesion: 0.15
Nodes (16): AuthenticatedUser, get_obo_token(), get_security_manager(), get_verified_user_context(), Any, Request, FastAPI dependencies for Databricks OBO identity + Concierge SP handoff. Soft-…, Concierge: validate entitlements, return SP client (drop OBO token). (+8 more)

### Community 17 - "OpenCode MCP Config"
Cohesion: 0.09
Nodes (22): enabled, type, url, instructions, mcp, docs-langchain, reference-langchain, enabled (+14 more)

### Community 18 - "force-graph Layout"
Cohesion: 0.10
Nodes (23): Br(), cr(), ei(), Gr(), hi(), jr(), kr(), li() (+15 more)

### Community 19 - "marked.js Tokens"
Cohesion: 0.22
Nodes (21): copy(), d(), dr(), F(), g(), ga(), jt(), kt() (+13 more)

### Community 20 - "Connector Exceptions"
Cohesion: 0.14
Nodes (18): ConnectorError, Exception, RateLimitError, Shared exceptions for ``databricks_connectors``., HTTP 429 / RESOURCE_EXHAUSTED after retries exhausted., Explicit ``.rest()`` gateway failure (non-retryable or exhausted)., Base error for ``databricks_connectors``., RestError (+10 more)

### Community 21 - "Document Text Service"
Cohesion: 0.15
Nodes (9): DocumentTextService, Any, Path, Pure document markdown / chunk text operations. No agent session state, no…, Production helpers for overview, search, and excerpt over extracted text.…, Return a character-range slice of markdown with offset metadata., Resolve ``_meta.json`` path from doc metadata or sibling of markdown., Format metadata + short markdown preview for agent consumption. (+1 more)

### Community 22 - "Builder Chat UI"
Cohesion: 0.34
Nodes (14): appendMessage(), applyDefinition(), bindDropzone(), build(), el(), ensureProject(), escapeHtml(), fmtSize() (+6 more)

### Community 23 - "Profile Page UI"
Cohesion: 0.36
Nodes (14): assetRow(), escapeHtml(), initials(), loadIdentity(), loadSection(), metaRow(), refreshAll(), renderAi() (+6 more)

### Community 24 - "CLI Token Cache"
Cohesion: 0.21
Nodes (11): _cache_key(), clear_cli_oauth_token_cache(), _expiry_epoch(), get_cached_cli_oauth_token(), peek_cached_cli_oauth_token(), Any, In-process TTL cache for local Databricks CLI OAuth tokens.…, Return a local CLI OAuth access token, cached until near expiry. Concurrent… (+3 more)

### Community 25 - "New Project Form UI"
Cohesion: 0.39
Nodes (11): addReqRow(), bindDropzone(), build(), collectRequirements(), el(), escapeHtml(), fmtSize(), kindOf() (+3 more)

### Community 26 - "Usage Dedup Patch"
Cohesion: 0.25
Nodes (10): _astream_with_lookahead(), install_usage_dedup_patch(), Any, One-chunk lookahead deduplication of input_tokens in streamed responses. The…, Return a copy of chunk with input_tokens and total_tokens zeroed. Args: chunk:…, Wrap _stream with one-chunk lookahead to filter usage on non-final chunks., Wrap _astream with one-chunk lookahead to filter usage on non-final chunks., Install one-chunk lookahead filter on ChatOpenAI. Idempotent: subsequent calls… (+2 more)

### Community 27 - "HTTPX Auth Client"
Cohesion: 0.20
Nodes (6): AsyncClient, Client, DatabricksHttpxAuth, Request, Response, Bridge SDK ``authenticate()`` into sync/async httpx clients.

### Community 28 - "Log Redaction Filters"
Cohesion: 0.22
Nodes (8): install_databricks_log_redaction(), LogRecord, Log filters that redact Databricks credentials from log records., Strip secrets from log messages without false-positives on 'token_count'., Attach redaction filter to Databricks / connector / agent_server loggers., Redact secrets in an arbitrary string (for tests / ad-hoc scrubbing)., redact_secrets(), SensitiveDataRedactor

### Community 29 - "Dashboard Home UI"
Cohesion: 0.38
Nodes (9): escapeHtml(), fmtNodes(), fmtSpend(), load(), relTime(), rowHtml(), statusTag(), summaryLine() (+1 more)

### Community 30 - "Logger Namespace Registry"
Cohesion: 0.22
Nodes (8): get_namespace_config(), list_namespaces(), Any, Logger namespace registry and configuration. Provides a centralized registry of…, Register a new logger namespace at runtime. Args: name: Namespace name (e.g.,…, Get configuration for a specific namespace. Args: name: Namespace name Returns:…, List all registered namespaces with descriptions. Returns: Dict mapping…, register_namespace()

### Community 31 - "marked.js Helpers"
Cohesion: 0.36
Nodes (8): bn(), clamp(), dn(), formatHsl(), gn(), pn(), x(), xn()

### Community 32 - "Client Logger JS"
Cohesion: 0.60
Nodes (5): _emit(), _flush(), _scheduleFlush(), _shouldLog(), _ts()

### Community 33 - "API Fetch Wrapper JS"
Cohesion: 0.83
Nodes (3): raw(), _redirectToLogin(), _request()

### Community 34 - "Theme Toggle JS"
Cohesion: 1.00
Nodes (3): apply(), initToggle(), mode()

### Community 35 - "force-graph Canvas"
Cohesion: 0.67
Nodes (4): b(), go(), Qi(), vo()

## Knowledge Gaps
- **28 isolated node(s):** `$schema`, `AGENTS.md`, `.opencode/QUICKSTART.md`, `shell`, `.opencode/skills` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthProvider` connect `Databricks Auth Providers` to `Auth Bridge & Gateway Credentials`, `Environment Config Reader`, `Connector Hub`, `FastAPI Auth Dependencies`, `HTTPX Auth Client`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `ConnectorHub` connect `Connector Hub` to `Auth Bridge & Gateway Credentials`, `Identity & User Verification`, `Databricks Auth Providers`, `Environment Config Reader`, `Connector Exceptions`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `load_registries()` connect `Model Catalog Registry` to `Chat Model Wrapper (LangChain)`, `Auth Bridge & Gateway Credentials`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `n()` (e.g. with `ai()` and `bo()`) actually correct?**
  _`n()` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `e()` (e.g. with `ae()` and `ai()`) actually correct?**
  _`e()` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `EnvironmentConfig` (e.g. with `AuthProvider` and `DatabricksHttpxAuth`) actually correct?**
  _`EnvironmentConfig` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `qr()` (e.g. with `a()` and `i()`) actually correct?**
  _`qr()` has 6 INFERRED edges - model-reasoned connections that need verification._