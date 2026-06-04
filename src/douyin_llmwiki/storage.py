from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import StorageError


class BailianTemporaryFileStorage:
    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def upload_and_sign(self, path: Path, object_key: str) -> str:
        requests = _requests()
        policy_response = requests.get(
            f"{self.base_url}/uploads",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"action": "getPolicy", "model": self.model},
            timeout=60,
        )
        policy = _json_or_error(policy_response, "get Bailian temporary upload policy")
        policy_data = policy.get("data")
        if not isinstance(policy_data, dict):
            raise StorageError(f"Bailian upload policy response was not recognized: {policy}")

        key = f"{policy_data['upload_dir']}/{path.name}"

        with path.open("rb") as file_obj:
            files = {
                "OSSAccessKeyId": (None, policy_data["oss_access_key_id"]),
                "Signature": (None, policy_data["signature"]),
                "policy": (None, policy_data["policy"]),
                "x-oss-object-acl": (None, policy_data["x_oss_object_acl"]),
                "x-oss-forbid-overwrite": (None, policy_data["x_oss_forbid_overwrite"]),
                "key": (None, key),
                "success_action_status": (None, "200"),
                "file": (path.name, file_obj),
            }
            upload_response = requests.post(
                policy_data["upload_host"],
                files=files,
                timeout=300,
            )
        if upload_response.status_code >= 400:
            raise StorageError(
                "Failed to upload audio to Bailian temporary file storage: "
                f"HTTP {upload_response.status_code} {upload_response.text}"
            )

        return f"oss://{key}"

    def delete(self, object_key: str) -> None:
        return None


class LocalPathStorage:
    def upload_and_sign(self, path: Path, object_key: str) -> str:
        return str(path)

    def delete(self, object_key: str) -> None:
        return None


class OssStorage:
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str,
        signed_url_expires: int,
    ) -> None:
        try:
            import oss2
        except ImportError as exc:
            raise StorageError("oss2 is not installed. Run `pip install -e .` first.") from exc

        auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(auth, endpoint, bucket_name)
        self.signed_url_expires = signed_url_expires

    def upload_and_sign(self, path: Path, object_key: str) -> str:
        try:
            self.bucket.put_object_from_file(object_key, str(path))
            return self.bucket.sign_url("GET", object_key, self.signed_url_expires, slash_safe=True)
        except Exception as exc:
            raise StorageError(f"Failed to upload audio to OSS: {exc}") from exc

    def delete(self, object_key: str) -> None:
        try:
            self.bucket.delete_object(object_key)
        except Exception as exc:
            raise StorageError(f"Failed to delete temporary OSS object {object_key}: {exc}") from exc


def _requests():
    try:
        import requests
    except ImportError as exc:
        raise StorageError("requests is not installed. Run `pip install -e .` first.") from exc
    return requests


def _json_or_error(response: Any, action: str) -> dict[str, Any]:
    if response.status_code >= 400:
        raise StorageError(f"Failed to {action}: HTTP {response.status_code} {response.text}")
    try:
        data = response.json()
    except ValueError as exc:
        raise StorageError(f"Failed to {action}: response was not JSON") from exc
    if not isinstance(data, dict):
        raise StorageError(f"Failed to {action}: response JSON was not an object")
    return data
