# Azure Provisioning Request — CLL Initiative Dashboard

**To:** Georgia Tech A&I (cloud provisioning / scoping)
**From:** Kevin Wong, Associate Director of Strategic Operations, College of Lifetime Learning
**Date:** 2026-10-08
**Cost center:** [CLL cost center — to be confirmed]
**Attachment:** `docs/ops/AZURE_PROVISIONING.md` (full stack requirements, generated from the application)

---

## Summary

The **CLL Initiative Dashboard** is a Python web application supporting the
Dean's weekly leadership meetings across the College of Lifetime Learning. It
provides initiative tracking and reporting across the College, in support of
weekly leadership meetings and strategic decision-making.

We are requesting provisioning for **two environments — production and
development** — on the Georgia Tech tenant.

| Resource | Development | Production |
|---|---|---|
| **Resource group** | `rg-cll-dash-dev` | `rg-cll-dash-prod` |
| **App Service Plan** (Linux) | Basic **B1** | Standard **S1** |
| **Azure SQL Database** | Basic | Serverless **GP_S_Gen5_1** |
| **Azure Key Vault** | Standard | Standard |
| **Application Insights** | pay-as-you-go | pay-as-you-go |

**Shared across both:** a Log Analytics workspace and an Azure Monitor Action Group.

**Identity and access:** an Entra ID App Registration + Enterprise Application;
a system-assigned Managed Identity per Web App; the Entra ID admin and app
identity on Azure SQL (AAD-only auth); and RBAC assignments for the CLL team.

**Networking:** a custom domain with a managed certificate for production (DNS
via GT OIT), and a managed database reachable privately if the data
classification requires it.

**Estimated cost:** ~$100–185/month for both environments (~$20–35/month
development, ~$80–140/month production), pay-as-you-go, pending the GT Azure
agreement.

**User load is low:** ~40 registered users, ≤25 concurrent.

---

## Guidance requested before this request is final

1. **Subscription, tenant and region** — which subscription should this be
   provisioned under? We propose **East US 2** (nearest Azure region to Atlanta),
   but the region is OIT's to select.
2. **Private endpoint** — is one required for the database, given the data
   classification of this workload?
3. **Custom domain** — confirm the GT hostname (`*.gatech.edu`); the **DNS record
   is a GT OIT lead-time item** and the longest-lead external dependency.
4. **RBAC** — confirm the roles and CLL principals for the team's assignments.
5. **Identity** — confirm the App Registration and each app's managed identity
   can be created under the chosen subscription.

The attached provisioning document (`AZURE_PROVISIONING.md`) has the full
technical detail needed for your review. Happy to schedule a scoping call with
A&I at your convenience.
