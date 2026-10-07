# Azure Provisioning Request — CLL Initiative Dashboard

**To:** Georgia Tech A&I (cloud provisioning / scoping)
**From:** Kevin Wong, Associate Director of Strategic Operations, College of Lifetime Learning
**Date:** 2026-10-07
**Cost center:** [CLL cost center — to be confirmed]
**Attachment:** `docs/ops/AZURE_PROVISIONING.md` (full stack requirements, generated from the codebase)

---

> **Time-sensitive:** The current app is returning 403 to all users. October 16 is the next Dean's leadership meeting — the hard deadline for resolution.

---

## The core problem

The **CLL Initiative Dashboard** is a Python/FastAPI web application supporting the Dean's weekly leadership meetings across the College of Lifetime Learning. It is currently running on a **personal Azure for Students subscription outside the Georgia Tech tenant**, creating two blocking conditions:

- **Availability:** the free-tier F1 plan has hit its stop-request quota (80/15) and returns **403 to all users**.
- **Data policy:** GT has not cleared personal-subscription hosting for institutional use.

Both must be resolved before October 16.

---

## Summary of what's needed

| Resource | Proposed |
|---|---|
| **App Service Plan** | Standard **S1** Linux (or Basic **B1** as an interim to unblock the outage) |
| **Azure SQL Database** | Serverless **GP_S_Gen5_1** (or Basic for the demo phase) |
| **Azure Key Vault** | Two secrets currently in plaintext (`APP_PASSCODE`, `APP_SECRET`); the SQL connection string will be created into Key Vault from the outset |
| **Application Insights + Log Analytics** | No telemetry exists today — `/healthz` is the only signal |
| **Estimated cost** | ~$80–140/month at launch; ~$20–35/month on the interim tier |

**User load is low:** ~40 registered users, ≤25 concurrent.

---

## Future needs — request now, to avoid a second procurement cycle

These are **not needed on day one**, but each has a lead time owned by another team (Identity, OIT/DNS, security). Provisioning them in this request — even if the app does not use them for weeks — avoids a repeat review before the December/January board cycle.

| Future need | Why request it now | Cost | Lead-time owner |
|---|---|---|---|
| **Entra ID App Registration** (+ Enterprise Application) | Institutional SSO is the expected end-state; the app's current shared passcode is a prototype gate. The registration itself is free and taking it now lets the SSO code change proceed without a new request. | $0 | GT Identity |
| **System-assigned Managed Identity** on the Web App | Lets the app read Key Vault and authenticate to Azure SQL **without any password** (AAD token auth). This is the recommended production posture and removes the connection-string secret entirely. | $0 | A&I |
| **Entra ID admin + app identity on Azure SQL** (AAD-only auth) | Required for passwordless DB access from the managed identity. Can be enabled at provisioning; password auth disabled later. | $0 | A&I |
| **Custom domain + App Service Managed Certificate** | A GT service should present `*.gatech.edu`, not `*.azurewebsites.net`. Certificate is free and auto-renewing; the **DNS record must be created by GT OIT** — that is the lead-time item. | $0 (cert) | GT OIT / DNS |
| **Azure Monitor Action Group** → GT email/Teams | Application Insights is requested, but without an action group its alerts go nowhere. One action group routes failures and health alerts to the CLL team. | $0 | A&I |
| **Log Analytics workspace** | Already requested (above); listed here because it is the retention/privacy boundary the security review will ask about. | see above | A&I |

**Code changes these imply (owned by this project, not by A&I):** a SQL driver (`pyodbc` or `pymssql`) and `azure-identity` added to the runtime; auth switched from the shared passcode to Entra token validation. None of these block provisioning — they are noted so the resource request and the roadmap agree.

---

## Guidance requested before this request is final

1. **GT subscription/tenant** — which subscription should this be provisioned under?
2. **Region** — proposing **East US 2** (nearest Azure region to Atlanta); confirm or redirect.
3. **Private endpoint** — is one required for the database given the data classification of this workload?
4. **Entra ID / managed identity** — confirm the App Registration and app managed identity can be created under the chosen subscription now, even though the SSO code lands later.

The attached provisioning document (`AZURE_PROVISIONING.md`) has the full technical detail needed for your review. Happy to schedule a scoping call with A&I at your convenience.
