# ERPNext Docker Test Bed

These are disposable local stacks for ERPNext, Lumen Restaurants, and URY. Each uses a pinned source snapshot, a separate Compose project and named volumes, and loopback-only browser access. They are evaluation environments, not production deployments; do not use real customer or payment data.

Start or refresh the stack from PowerShell:

```powershell
.\scripts\erpnext-testbed.ps1 -Action up
```

The ERPNext UI is at `http://127.0.0.1:18080`. Sign in as `Administrator`; the generated password is stored at `%TEMP%\lumina-erpnext-testbed-admin-password.txt`. The site name is `frontend`.

Run the real, read-only actor-liveness probe after installing the project in the selected Python environment:

```powershell
$env:PYTHONPATH = "C:/path/to/lumina-biz/src"
python .\scripts\erpnext-testbed-smoke.py
```

Check service status:

```powershell
.\scripts\erpnext-testbed.ps1 -Action status
```

Read site bootstrap logs separately:

```powershell
.\scripts\erpnext-testbed.ps1 -Action logs
```

Remove the stack and its test data:

```powershell
.\scripts\erpnext-testbed.ps1 -Action down
```

The `down` action deletes only the `lumina-erpnext-test` Compose project and its named volumes. The upstream Compose file is downloaded to the system temp directory at a pinned `frappe_docker` revision. The smoke probe creates a temporary API secret in memory and rotates it after the check.

## Restaurant App Evaluations

The Lumen Restaurants candidate and URY run in separate projects and sites, both based on ERPNext 16.60.0. Their source revisions, observed issues, and evaluation limits are recorded in [lumen-evaluation.md](lumen-evaluation.md).

Start or inspect Lumen Restaurants:

```powershell
.\testbed\lumen-evaluation.ps1 -Action up -Candidate lumen
.\testbed\lumen-evaluation.ps1 -Action status -Candidate lumen
```

Lumen Restaurants is at `http://127.0.0.1:18081/pos`; its temporary Administrator password is stored in `%TEMP%\lumina-lumen-evaluation-secrets.json` under `administrator`. Verify the synthetic table-to-kitchen-to-invoice flow:

```powershell
.\testbed\lumen-restaurant-probe.ps1
```

Start or inspect URY:

```powershell
.\testbed\lumen-evaluation.ps1 -Action up -Candidate ury
.\testbed\lumen-evaluation.ps1 -Action status -Candidate ury
```

URY is at `http://127.0.0.1:18082/pos`; its temporary Administrator password is stored in `%TEMP%\lumina-ury-evaluation-secrets.json` under `administrator`. The seeded cashier login is `cashier@ury.com`; its local password is in `%TEMP%\lumina-ury-cashier-password.txt`.

Remove an evaluation project and only its data/credentials:

```powershell
.\testbed\lumen-evaluation.ps1 -Action down -Candidate lumen
.\testbed\lumen-evaluation.ps1 -Action down -Candidate ury
```

Each `down` action is scoped to the named candidate project; it does not affect the original `lumina-erpnext-test` project.