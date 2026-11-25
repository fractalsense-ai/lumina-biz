# Lumen Restaurants Evaluation

This is an isolated experiment, not a production deployment or an adoption decision. It uses ERPNext 16.60.0 and Lumen Restaurants 0.1.0-r18 from the publicly accessible `abdullla00/LumenRestaurants` snapshot at commit `083820186e282e76add31d3c30fd0e62ca35cd32`. Its relationship to the vendor's currently unavailable documented upstream has not been verified. The app is AGPL-3.0-only; review licensing and trademarks before distribution or adoption.

The evaluation uses the Compose project `lumina-lumen-eval`, separate volumes, and `http://127.0.0.1:18081`. Backend services use an internal Docker network; the frontend additionally uses an ingress network for loopback publishing. The original `lumina-erpnext-test` project and its data are separate.

Build and start from this repository's root:

```powershell
docker build -t lumina-lumen-evaluation:local -f testbed/lumen-restaurants.Dockerfile testbed
.\testbed\lumen-evaluation.ps1 -Action up
```

Sign in as `Administrator` using the `administrator` value in `%TEMP%\lumina-lumen-evaluation-secrets.json`. The file also holds the evaluation database password; keep it private. Running `up` again preserves the evaluation volumes and credentials. Use `-Action status` for container status.

## Observed Results

- The app installed and `/pos` and its bundled JavaScript returned HTTP 200 on ERPNext 16.60.0.
- On the seeded test site, an authenticated HTTP probe created a table order and a linked kitchen ticket, then submitted a simulated cash payment. ERPNext recorded a paid POS Invoice and the restaurant order closed with the invoice linked.
- The synthetic shift closed with matching simulated counts. Its POS Closing Entry was submitted and the two restaurant POS Invoices were consolidated into a Sales Invoice. No physical payment or printer was involved.
- The vendor's sample builder needed ERPNext 16 stock serial/batch activation and POS Settings set to `POS Invoice`. Its historical sample sales were rejected because their posting dates preceded the current opening entries; its gift-card samples failed account-type validation. A current-day sample sale posted. The sample uses a Saudi company and VAT, not a validated US configuration.
- The vendor's guide says restaurant-mode tables, tickets, and bookings need connectivity to the ERPNext server; its retail offline queue is not proof of offline restaurant operation.

The probe at `testbed/lumen-restaurant-probe.ps1` creates new synthetic orders, kitchen tickets, and POS invoices on each run. It checks that port 18081 belongs to this evaluation project. A configured sample outlet with an open register is required; run only on disposable evaluation data.

Still to evaluate: maintainable source provenance, permissions and actor isolation, reconciliation after failure, internet-versus-LAN outages, payment terminal and printer hardware, tax and tip rules, offline behavior, and comparison with URY. No results above establish production suitability.

## URY Comparison

The separate `lumina-ury-eval` project runs ERPNext 16.60.0 with URY `3.0.0-beta.2` from the official `version-16` branch pinned at `100c43fe2e52b21e41523c61e7fc1902baa96940`. This is a branch snapshot, not the `v3.0.0-beta.2` tag. The POS, kitchen, and main setup frontend assets were built into the image; other frontend packages were not built. HRMS and the optional payments app were not installed.

```powershell
docker build -t lumina-ury-evaluation:local -f testbed/ury-evaluation.Dockerfile testbed
.\testbed\lumen-evaluation.ps1 -Action up -Candidate ury
```

The setup wizard is at `http://127.0.0.1:18082/ury/setup-wizard/0`. Sign in as `Administrator` using the `administrator` value in `%TEMP%\lumina-ury-evaluation-secrets.json`. The bare `/ury` route returned 404; the setup wizard, `/pos`, and `/mosaic` returned HTTP 200 with their generated JavaScript assets. The URY site is separate from Lumen and the original ERPNext site.

- URY's built-in demo wizard failed while creating a Purchase Order with `KeyError: 'Purchase Order'` in ERPNext's return-charges code. Its separate seeder created sample restaurant records and paid invoices, but logged historical-sale failures due to POS opening-entry dates and skipped daily P&L because HRMS was absent.
- Seeded URY KOTs refer to draft POS Invoices. A complete table-to-payment-to-shift-close flow has not been verified for URY, so these results are not directly comparable to the completed Lumen cash-flow probe.
- URY's v16 branch declares ERPNext/Frappe 16 support, while its installation guide still references v15 and HRMS. Its README advertises offline POS and kitchen features, but offline behavior, payment and printing hardware, and permissions were not tested.
- Lumen Restaurants' pinned snapshot identifies itself as AGPL-3.0-only. URY's pinned repository `LICENSE` is AGPL-3.0, but its Frappe app hook metadata declares `MIT`; this is an unresolved license inconsistency. Confirm both exact revisions with their maintainers and obtain legal advice before adoption, distribution, or network deployment of modifications.