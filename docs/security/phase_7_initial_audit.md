# Udyam360 — Phase 7 Initial Pre-Implementation Security Audit
**Baseline Audit of Customer Identity, Session Security, Admin Authentication & Persistence**  
**Date:** 2026-11-07  
**Scope:** Phase 7 Hardening Baseline (`backend/app/`, `frontend/src/`)  
**Status:** Audit Completed — Baseline Established

---

## 1. Existing Security Architecture

The current Udyam360 implementation sits between a pure hackathon prototype and an authenticated web application:

1. **Frontend Presentation Layer (`frontend/src/`):**
   - React + TypeScript Single Page Application (SPA) bundled with Vite.
   - Onboarding state is tracked via `OnboardingContext.tsx` and mirrored into browser `sessionStorage` (`udyam360_conv_id`, `udyam360_profile`, `udyam360_session_token`).
   - Axios instance in `client.ts` intercepts requests to attach `X-Session-Token` and reads response headers to save issued tokens.
   - Admin API calls in `frontend/src/api/admin.ts` still send a hardcoded `ADMIN_CONFIG` header (`'X-Admin-Role': 'ExecutiveAdmin'`).
2. **FastAPI Application Layer (`backend/app/main.py`):**
   - Exposes REST endpoints across `/advisor`, `/kyc`, `/orders`, `/catalogue`, `/recommendations`, `/quotes`, and `/admin`.
   - CORS middleware restricts origins to `localhost` and `127.0.0.1` dev ports, with credentials enabled.
   - Lacks CSRF middleware, rate limiting middleware, and HTTP security headers (CSP, X-Frame-Options, HSTS).
3. **In-Memory Core Stores (`backend/app/services/`):**
   - `conversation_service._sessions`: In-memory `Dict[str, ConversationState]`.
   - `kyc_orchestrator._cases`: In-memory `Dict[str, KYCCaseResponse]`.
   - `order_service._orders_by_id`: In-memory `Dict[str, OrderRecord]`.
   - `security_manager._owned_cases`: In-memory `Dict[str, Set[str]]`.
   - State resets entirely on application server restart.
4. **Air-Gapped Local OCR & Private Disk Storage:**
   - Optical character recognition executes 100% locally on CPU via `WinOCRProvider` or `RapidOCRProvider` (`backend/app/services/ocr/`).
   - Zero document buffers, images, or extracted raw streams are ever transmitted to Google Gemini.
   - Uploaded document files are stored in `backend/storage/kyc_documents/{case_id}/`.

---

## 2. Existing Authentication Mechanisms

1. **Customer Authentication:**
   - **Current State:** There is **no customer login, registration, or passwordless OTP system**.
   - Identity is anchored solely to transient session identifiers (`conv_...`, `KYC-...`, `ord_...`).
   - HMAC-SHA256 signed session tokens are issued at `/advisor/start`, `/kyc/cases`, and `/orders`, but these are tied only to browser sessions, not verified customer identities or phone numbers.
2. **Admin Authentication:**
   - **Current State:** Relying on the `X-Admin-Role` request header (`ExecutiveAdmin`, `Admin`, `SalesManager`).
   - While the default header bypass was patched in Phase 6.1 (omitted header returns 403), any client that sends the string `X-Admin-Role: ExecutiveAdmin` is granted full administrative access.
   - There are no administrator credentials, password hashes, admin login forms, or cryptographic admin session tokens.

---

## 3. Existing Customer Ownership Implementation

1. **Session-to-Resource Binding (`backend/app/core/security.py`):**
   - `SessionSecurityManager` maintains three in-memory dictionaries: `_owned_cases`, `_owned_orders`, and `_owned_conversations`.
   - Dependencies `require_case_access`, `require_order_access`, and `require_conversation_access` verify that the caller's session token owns the target ID.
2. **Limitations:**
   - Ownership records live in volatile memory. A backend restart or worker process reload purges all ownership records while encrypted files remain on disk.
   - There is no persistent `Customer` entity in a database linking a verified phone number to their past and active orders or KYC cases.
   - Session identifiers are stored in JavaScript-accessible `sessionStorage` and sent via `X-Session-Token` headers rather than HttpOnly cookies.

---

## 4. Existing Admin Authorization

1. **Guard Implementation (`backend/app/api/admin.py` L34-51):**
   - `verify_admin_access(x_admin_role: Optional[str] = Header(None))` checks if the header string matches `["executiveadmin", "admin", "salesmanager"]`.
2. **Security Deficiencies:**
   - An HTTP request header cannot serve as authentication. Anyone reading the API documentation or inspecting network traffic can set `X-Admin-Role: ExecutiveAdmin`.
   - No password verification, no multi-factor authentication, no session expiration, and no role assignment table.

---

## 5. Existing KYC Encryption and Key Storage

1. **Encryption at Rest (`backend/app/services/kyc_storage_service.py` L115-135):**
   - Implemented using `cryptography.fernet.Fernet` (AES-128-CBC + HMAC-SHA256).
   - `save_document()` encrypts raw binary bytes before writing to `backend/storage/kyc_documents/{case_id}/{doc_id}.{ext}`.
   - `read_document_bytes()` decrypts the stored ciphertext into memory for local OCR extraction.
2. **Key Storage:**
   - The master key is derived via `hashlib.sha256()` from `settings.SECRET_KEY` or `settings.KYC_ENCRYPTION_KEY`.
   - *Limitation:* If neither is configured in environment variables, it falls back to a hardcoded string default (`"udyam360-kyc-master-vault-2026"`). There is no fail-safe preventing startup without a configured secret in production.

---

## 6. Existing Data Persistence

1. **Database Infrastructure:**
   - **Current State:** **None.** The project currently has zero relational or document database tables.
   - All customer profiles, conversation turns, KYC cases, consent records, orders, and ownership mappings are stored in plain in-memory Python dictionaries.
2. **Persistence Vulnerability:**
   - When the backend process restarts (e.g., during deployment, crash, or reload), all session state, active orders, and KYC records are wiped. Encrypted document files remain on disk as orphans with lost metadata.

---

## 7. Existing CORS and CSRF Configuration

1. **CORS (`backend/app/main.py` L27-46):**
   - Origin whitelist: `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:8000`, `http://127.0.0.1:8000`.
   - `allow_credentials=True`.
   - `allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"]`.
2. **CSRF:**
   - **Current State:** **Completely missing.** There is no CSRF middleware, no CSRF cookie, and no CSRF header validation. Because sessions currently rely on headers (`X-Session-Token`), standard browsers do not send headers cross-origin automatically. However, moving to `HttpOnly` cookies makes CSRF defense mandatory.

---

## 8. Existing Security Test Coverage

1. **Existing Test Suites:**
   - `backend/tests/test_security_remediations.py` (10 tests):
     - Admin missing header rejection.
     - Customer A / Customer B IDOR cross-access blocking.
     - Pre-consent document upload blocking.
     - Fernet encryption at rest verification.
     - Public tracking PII masking (phone, email, address).
     - Token signature tampering rejection.
   - `backend/tests/test_kyc_security.py` (5 tests):
     - Path traversal filename sanitization.
     - File size limit (10 MB).
     - Magic byte deep validation.
     - Invalid extension rejection.
     - Pillow image corruption checks.
2. **Test Coverage Gaps:**
   - Zero tests for customer OTP request, delivery, expiration, replay, attempt limits, or lockout.
   - Zero tests for real admin login, password hashing, and session cookie validation.
   - Zero tests for CSRF token validation or cross-origin state changes.
   - Zero tests for rate-limiting enforcement.
   - Zero tests for database persistence and restart recovery.

---

## 9. Comprehensive Gaps to be Addressed in Phase 7

| Security Dimension | Current Gap | Phase 7 Target Architecture |
| :--- | :--- | :--- |
| **Customer Identity** | No login; anonymous session-based onboarding. | Passwordless Indian mobile OTP authentication (`MockOTPProvider` / `SMSOTPProvider` interface) creating persistent `Customer` records. |
| **Session Transport** | JavaScript-accessible `X-Session-Token` header. | `HttpOnly`, `SameSite=Lax`, `Secure` session cookies with inactivity (30m) and absolute (8h) timeouts. |
| **CSRF Defense** | Zero CSRF protections. | Cryptographic Double Submit Cookie / CSRF token validation on all state-changing endpoints. |
| **Admin Authentication** | Trust in spoofable `X-Admin-Role` header. | Separate admin login (`/auth/admin/login`), Argon2id/PBKDF2 hashed credentials, login attempt limits, admin session cookies. |
| **Data Persistence** | In-memory volatile Python dictionaries. | SQLite + SQLAlchemy persistent database (`udyam360.db`) storing Customers, Sessions, Consent history, KYC metadata, Orders, and Audit logs. |
| **Rate Limiting** | No rate limits on any endpoint. | Token bucket / sliding window rate limiting on OTP requests, OTP verifications, Admin login, and Public tracking. |
| **Security Headers** | Standard FastAPI defaults without security headers. | Security middleware adding CSP, X-Content-Type-Options, Referrer-Policy, and cache-control guards. |
| **Audit Logging** | Generic application logging. | Structured Security Audit Log table & service recording auth, consent, KYC validation, order transitions, and admin actions without sensitive data leakage. |
| **Frontend Auth Experience** | No login screen or OTP prompt. | Mobile number + OTP modal/step prior to KYC; separate Admin Login screen; protected routes; HttpOnly cookie integration. |

---
*Audit recorded. Proceeding with Phase 1 through Phase 11 implementation.*

