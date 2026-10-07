# Azure Provisioning Request — CLL Initiative Dashboard

**To:** Georgia Tech A&I (cloud provisioning / scoping)
**From:** CLL Initiative Dashboard project
**Date:** 2026-10-07
**Attachment:** `docs/ops/AZURE_PROVISIONING.md` (full stack requirements, generated from the codebase)

---

I'm requesting Azure resources for the **CLL Initiative Dashboard**, a Python/FastAPI web application that supports the Dean's weekly leadership meetings across the College of Lifetime Learning.

## The core problem

The app is currently running on a **personal Azure for Students subscription outside the Georgia Tech tenant**. This is a blocking issue:

- **Data-policy:** GT has not cleared personal-subscription hosting for institutional use.
- **Availability:** the free-tier **F1** plan has hit its stop-request quota (**80 / 15**) and returns **403 to all users**.

Both conditions must be resolved before **October 16**.

## Summary of what's needed

| Resource | Proposed |
|---|---|
| **App Service Plan** | Standard **S1** Linux (or Basic **B1** as an interim to unblock the outage) |
| **Azure SQL Database** | Serverless **GP_S_Gen5_1** (or Basic for the demo phase) |
| **Azure Key Vault** | Two secrets currently in plaintext (`APP_PASSCODE`, `APP_SECRET`); the SQL connection string will be created into Key Vault from the outset |
| **Application Insights + Log Analytics** | No telemetry exists today — `/healthz` is the only signal |
| **Estimated cost** | **~$80–140/month** at launch; **~$20–35/month** on the interim tier |

**User load is low:** ~40 registered users, **≤25 concurrent**.

## Guidance requested

1. **Which GT subscription/tenant** to provision under.
2. **Preferred region** — proposing **East US 2**, the Azure region nearest Atlanta (Georgia has no Azure region; East US / East US 2 are both in Virginia).
3. **Whether a private endpoint is required** for the database given the data classification.

Happy to schedule a scoping call with A&I. The attached provisioning document (`AZURE_PROVISIONING.md`) has everything needed for the technical review.
