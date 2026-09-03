# Publication Checklist

Use this checklist before changing the repository visibility from private to public.

## Repository history

- [ ] Confirm this repository contains only the clean reconstruction history.
- [ ] Confirm the original private repository and its `.git` history were never copied into this repository.
- [ ] Review commit messages for customer names, internal project names, ticket references, generated task URLs, or other historical context that should remain private.
- [ ] Confirm no old feature branch with unsanitized files will be exposed as part of the public repository.

## Credentials and identifiers

Search the entire repository and Git history for:

- [ ] HubSpot private-app tokens.
- [ ] Microsoft Entra client secrets.
- [ ] Tenant IDs from the original environment.
- [ ] Client/application IDs from the original environment.
- [ ] Real Dataverse organization/environment URLs.
- [ ] HubSpot list IDs from the original implementation.
- [ ] GCP project IDs, bucket names, service-account addresses, or deployment URLs tied to the original organization.
- [ ] API keys, passwords, connection strings, certificates, private keys, or bearer tokens.

`.env.example` must contain placeholders only.

## Customer and organization data

- [ ] No customer/company name from the original implementation.
- [ ] No real contact names, emails, phone numbers, addresses, CRM GUIDs, or exported records.
- [ ] No screenshots containing private CRM data.
- [ ] No logs copied from production.
- [ ] No support tickets, emails, internal documents, or business-process notes from the original organization.

## Dataverse schema

- [ ] The original property mapping file is not present.
- [ ] No proprietary Dataverse custom logical names remain in source, tests, documentation, or Git history.
- [ ] Sample custom fields are clearly fictional/generic.
- [ ] No internal program, period, campaign, product, department, or workflow labels reveal the original business schema.

## Source code

- [ ] No hard-coded environment URL.
- [ ] No hard-coded production record IDs.
- [ ] No customer-specific validation rules.
- [ ] No obsolete debug payloads or data dumps.
- [ ] No comments referring to the original customer, private incidents, internal personnel, or private infrastructure.
- [ ] No AI task URLs, prompt fragments, generated branch names, or comments such as `NEW`, `MODIFIED`, `replace this`, or tutorial-style notes.
- [ ] Code comments exist only where they explain a non-obvious technical constraint or design decision.

## Tests

- [ ] Test records are synthetic.
- [ ] Example names, emails, phone numbers, and IDs are fictional.
- [ ] Tests do not require production credentials.
- [ ] `pytest` passes from a clean environment.
- [ ] `ruff check .` passes.
- [ ] GitHub Actions is green on the final `main` commit.

## Documentation

- [ ] README accurately describes implemented behavior.
- [ ] README distinguishes the 2025 enterprise implementation from the later public reconstruction.
- [ ] No claim implies that reconstructed reliability/deployment features existed exactly this way in the original production code unless supported by evidence.
- [ ] No unverifiable scale, SLA, throughput, revenue, customer-count, or performance claims.
- [ ] Known limitations are documented.
- [ ] Deployment examples use placeholders rather than a real cloud environment.

## Security posture

- [ ] Historical HubSpot tokens found in the private archive have been revoked/rotated if they could still be valid.
- [ ] Historical Microsoft Entra client secrets found in the private archive have been revoked/expired/rotated if they could still be valid.
- [ ] No sensitive value was merely removed from the latest file while remaining in this repository's Git history.
- [ ] Secret Manager is documented as the deployment mechanism for runtime secrets.

## Portfolio review

Before publication, read the repository as an interviewer would:

- [ ] The project demonstrates integration architecture and engineering judgment without exposing the customer.
- [ ] The code is small enough to follow and does not look artificially over-engineered.
- [ ] The README explains why key choices were made rather than presenting a feature list only.
- [ ] The project can be defended technically in an interview.
- [ ] The repository does not claim to be the exact original enterprise source code.

## Final gate

Do not make the repository public until all items above have been reviewed and the final repository/history scan is clean.
