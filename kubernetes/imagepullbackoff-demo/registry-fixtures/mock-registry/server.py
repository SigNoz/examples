import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


CONFIG = json.dumps(
    {
        "architecture": "arm64",
        "config": {"Cmd": ["/bin/sh"]},
        "os": "linux",
        "rootfs": {"type": "layers", "diff_ids": ["sha256:" + "2" * 64]},
    },
    separators=(",", ":"),
).encode()
CONFIG_DIGEST = "sha256:" + hashlib.sha256(CONFIG).hexdigest()
DECLARED_LAYER_DIGEST = "sha256:" + "1" * 64
CORRUPT_LAYER = b"this-is-not-the-declared-layer"

RUNTIME_MANIFEST = json.dumps(
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": CONFIG_DIGEST,
            "size": len(CONFIG),
        },
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": DECLARED_LAYER_DIGEST,
                "size": len(CORRUPT_LAYER),
            }
        ],
    },
    separators=(",", ":"),
).encode()

PLATFORM_INDEX = json.dumps(
    {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [
            {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": "sha256:" + "3" * 64,
                "size": 512,
                "platform": {"architecture": "s390x", "os": "linux"},
            }
        ],
    },
    separators=(",", ":"),
).encode()


class RegistryHandler(BaseHTTPRequestHandler):
    server_version = "ImagePullBackOffMockRegistry/1.0"

    def log_message(self, format_string, *args):
        print(format_string % args, flush=True)

    def send_payload(self, status, payload=b"", content_type="application/json", digest=None):
        self.send_response(status)
        self.send_header("Docker-Distribution-Api-Version", "registry/2.0")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        if digest:
            self.send_header("Docker-Content-Digest", digest)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def handle_request(self):
        path = self.path.split("?", 1)[0]

        if path in ("/v2", "/v2/"):
            self.send_payload(200, b"{}")
            return

        if path.startswith("/v2/rate-limited/"):
            payload = json.dumps(
                {"errors": [{"code": "TOOMANYREQUESTS", "message": "image pull rate limit exceeded"}]},
                separators=(",", ":"),
            ).encode()
            self.send_payload(429, payload)
            return

        if path.startswith("/v2/platform-mismatch/app/manifests/"):
            digest = "sha256:" + hashlib.sha256(PLATFORM_INDEX).hexdigest()
            self.send_payload(200, PLATFORM_INDEX, "application/vnd.oci.image.index.v1+json", digest)
            return

        if path.startswith("/v2/runtime-failure/app/manifests/"):
            digest = "sha256:" + hashlib.sha256(RUNTIME_MANIFEST).hexdigest()
            self.send_payload(200, RUNTIME_MANIFEST, "application/vnd.oci.image.manifest.v1+json", digest)
            return

        if path == f"/v2/runtime-failure/app/blobs/{CONFIG_DIGEST}":
            self.send_payload(200, CONFIG, "application/vnd.oci.image.config.v1+json", CONFIG_DIGEST)
            return

        if path == f"/v2/runtime-failure/app/blobs/{DECLARED_LAYER_DIGEST}":
            self.send_payload(200, CORRUPT_LAYER, "application/vnd.oci.image.layer.v1.tar+gzip", DECLARED_LAYER_DIGEST)
            return

        payload = b'{"errors":[{"code":"MANIFEST_UNKNOWN","message":"not found"}]}'
        self.send_payload(404, payload)

    do_GET = handle_request
    do_HEAD = handle_request


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 5001), RegistryHandler).serve_forever()
