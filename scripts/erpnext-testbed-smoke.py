from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

import httpx
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from lumina.api import config as api_config
from lumina.api.dependencies import get_active_operating_context
from lumina.auth import auth as auth_module
from lumina.business_ops.connectors.erpnext.runtime import create_erpnext_actor_liveness_runtime

BASE_URL = "http://127.0.0.1:18080"
ORGANIZATION_ID = "lumina-docker-test"
SITE_ID = "frontend"
ACTOR_ID = "Administrator"
KEY_ENDPOINT = "/api/method/frappe.core.doctype.user.user.generate_keys"


def main() -> int:
    password_path = Path(tempfile.gettempdir()) / "lumina-erpnext-testbed-admin-password.txt"
    if not password_path.is_file():
        raise RuntimeError("Run scripts/erpnext-testbed.ps1 -Action up first.")

    client = httpx.Client(base_url=BASE_URL, timeout=15)
    runtime = None
    keys_created = False
    missing_verifier = object()
    previous_verifier = getattr(api_config, "ACTOR_LIVENESS_VERIFIER", missing_verifier)
    try:
        login = client.post(
            "/api/method/login",
            json={"usr": ACTOR_ID, "pwd": password_path.read_text(encoding="utf-8").strip()},
        )
        login.raise_for_status()

        key_response = client.post(KEY_ENDPOINT, json={"user": ACTOR_ID})
        key_response.raise_for_status()
        credentials = key_response.json()["message"]
        keys_created = True

        os.environ.update(
            {
                "LUMINA_ERP_ACTOR_LIVENESS_BASE_URL": BASE_URL,
                "LUMINA_ERP_ACTOR_LIVENESS_ORGANIZATION_ID": ORGANIZATION_ID,
                "LUMINA_ERP_ACTOR_LIVENESS_SITE_ID": SITE_ID,
                "LUMINA_ERP_ACTOR_LIVENESS_API_KEY": credentials["api_key"],
                "LUMINA_ERP_ACTOR_LIVENESS_API_SECRET": credentials["api_secret"],
            }
        )
        runtime = create_erpnext_actor_liveness_runtime()
        if runtime is None:
            raise RuntimeError("ERPNext actor-liveness runtime was not configured.")

        api_config.ACTOR_LIVENESS_VERIFIER = runtime.verifier
        original_jwt_secret = auth_module.JWT_SECRET
        original_user_jwt_secret = auth_module.USER_JWT_SECRET
        auth_module.JWT_SECRET = os.urandom(32).hex()
        auth_module.USER_JWT_SECRET = ""

        app = FastAPI()

        @app.get("/probe")
        async def probe(context: dict[str, str | None] = Depends(get_active_operating_context)):
            return context

        active_token = auth_module.create_scoped_jwt(
            ACTOR_ID,
            "operator",
            organization_id=ORGANIZATION_ID,
            site_id=SITE_ID,
        )
        mismatched_token = auth_module.create_scoped_jwt(
            ACTOR_ID,
            "operator",
            organization_id=ORGANIZATION_ID,
            site_id="wrong-site",
        )
        with TestClient(app) as api_client:
            active_response = api_client.get(
                "/probe",
                headers={"Authorization": f"Bearer {active_token}"},
            )
            if active_response.status_code != 200:
                raise RuntimeError("Active actor failed the protected HTTP probe.")
            active_context = active_response.json()
            if (
                active_context.get("organization_id") != ORGANIZATION_ID
                or active_context.get("site_id") != SITE_ID
            ):
                raise RuntimeError("Protected operating context returned the wrong scope.")

            mismatch_response = api_client.get(
                "/probe",
                headers={"Authorization": f"Bearer {mismatched_token}"},
            )
            if mismatch_response.status_code != 403:
                raise RuntimeError("Scope mismatch did not fail closed with HTTP 403.")

        print("active actor: allow; evidence_code=user_enabled")
        print("scope mismatch: denied with HTTP 403 through the protected HTTP dependency")
        return 0
    finally:
        if "original_jwt_secret" in locals():
            auth_module.JWT_SECRET = original_jwt_secret
            auth_module.USER_JWT_SECRET = original_user_jwt_secret
        if getattr(api_config, "ACTOR_LIVENESS_VERIFIER", missing_verifier) is getattr(runtime, "verifier", None):
            if previous_verifier is missing_verifier:
                delattr(api_config, "ACTOR_LIVENESS_VERIFIER")
            else:
                api_config.ACTOR_LIVENESS_VERIFIER = previous_verifier
        if runtime is not None:
            runtime.close()
        if keys_created:
            client.post(KEY_ENDPOINT, json={"user": ACTOR_ID}).raise_for_status()
            print("temporary API secret rotated")
        client.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERPNext liveness smoke test failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error