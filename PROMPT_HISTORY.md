# Prompt History — QR-Code-Gen

A chronological reference of the requests made while building this project, with a
short summary of what was done in response to each one. Useful for onboarding
teammates or explaining how this automation came together.

## Session 1 — Initial planning (2026-08-19)

**Prompt:**
> hello, you are a pro azure professional. I have a task that I do manually in azure.
> I get pdfs through the email and I generate a qr code for users to access them over
> the internet. I upload those pdfs to a storage account in azure. it can be found at
> kpcwebsitestorageaccount and Subscription ID 34ade81d-be2b-4c3e-846c-e646c78a09eb.
> I have created multiple containers in the storage account based on department.
> check the resources in azure using az cli read only commands and let's work on a
> way to automate this and agree on a plan.

**Outcome:** Az CLI wasn't installed. Attempted install, hit AlmaLinux 10 / RHEL
package compatibility issues.

**Prompt:** `try to install az cli through dnf`

**Prompt:** `you have passwordless sudo`

**Prompt:** `you are connected to different network, try now` *(x2)*

**Outcome:** Resolved by importing the correct `microsoft-2025.asc` signing key and
using the RHEL 10 Microsoft repo config, landing on Azure CLI 2.89.1.

**Prompt:** `go ahead you are logged in to azure, check out the initial prompt`

**Outcome:** Logged into Azure, inspected `kpcwebsitestorageaccount` read-only:
17 department containers, a Front Door/CDN profile fronting the account with
custom domains `cdn.kpc.com.kw` and `corporateblob.kpc.com.kw`, and existing
email-driven Function App automation elsewhere in the subscription. Proposed a
full plan: email ingestion → Service Bus → Function → blob upload → QR generation
→ delivery.

**Prompt:** `you know what, let's not worry about email sending now, we'll keep it as a future enhancement`

**Outcome:** Descoped to: user already has the PDF in hand → an AI agent (backed by
local Python scripts) resolves the department/container, validates input, uploads
the PDF, and generates a QR code — both saved locally and uploaded to Azure. Built:

- `scripts/containers.py` — canonical container list + department aliases
- `scripts/resolve.py` — fuzzy-matches folder/filename/user text to a real container
- `scripts/azure_blob.py` — blob upload wrapper (`DefaultAzureCredential`, no keys)
- `scripts/qr_publish.py` — CLI with `list-containers` / `check` / `publish`
- `.github/agents/qr-pdf-publisher.agent.md` — the "QR PDF Publisher" custom agent
- Fixed an RBAC gap (`Contributor` isn't enough for blob data-plane ops — added
  `Storage Blob Data Contributor`) and a URL-encoding bug in the generated QR link.
- Verified end-to-end with a real test PDF, then cleaned up the test blobs.

## Session 2 — First real publish + GitHub setup (2026-08-19)

**Prompt:** `@file:qr-pdf-publisher.agent.md publish the file @file:training_courses_non_listed_2026-2027.pdf`

**Outcome:** Published successfully to `employees-development` (inferred from
filename, confidence 0.9), with public URL, PDF blob, and QR code blob generated.

**Prompt:** `can u delete it, it was for testin`

**Outcome:** Deleted both blobs and the local QR PNG.

**Prompt:** `how to publish this agent in my github`

**Outcome:** Explained that a `.agent.md` file just needs to live in `.github/agents/`
inside a GitHub repo — no separate marketplace needed.

**Prompt:** `you do the steps`

**Outcome:** Initialized the local git repo and committed. Asked the user for a
GitHub repo URL/name and auth method before pushing.

**Prompt:** `cannt you access it and do it urself`

**Outcome:** Authenticated via `gh auth login` (device code flow, user completed
the browser authorization), created the repo, and pushed.

**Prompt:** `md file is not on gitgub`

**Outcome:** Confirmed the agent file *is* on GitHub at
[.github/agents/qr-pdf-publisher.agent.md](https://github.com/byturki/QR-Code-Gen/blob/main/.github/agents/qr-pdf-publisher.agent.md) —
it's just not surfaced on the repo's main page since GitHub doesn't feature the
`.github/agents` folder like it does `README.md` or `.github/workflows`.

## Session 3 — This session (2026-08-20)

**Prompt:** `i need to have our prompts history as a reference and share it over with people`

**Outcome:** This document.

---

**Repository:** https://github.com/byturki/QR-Code-Gen
