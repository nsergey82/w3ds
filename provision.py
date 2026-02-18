import requests
import uuid
import unittest
import os

DEMO_VERIFICATION_ID = "d66b7138-538a-465f-a6ce-f6985854c3f4"
REGISTRY_PORT = 4321
PROVISIONER_PORT = 3001


def get_entropy(registry_url: str) -> str:
    return requests.get(registry_url + "/entropy").json()["token"]


def provision(provisioner_endpoint: str, entropy: str, pubkey: str) -> str:
    namespace = uuid.uuid4()
    payload = {
        "registryEntropy": entropy,
        "namespace": namespace,
        "publicKey": pubkey,
        "verificationId": DEMO_VERIFICATION_ID,
    }
    return requests.post(provisioner_endpoint, data=payload).json()


def get_bearer_token(registry_url: str, platform: str) -> str:
    payload = {"platform": platform}
    return requests.post(registry_url + "/platforms/certification", json=payload).json()


class TestProvision(unittest.TestCase):
    def setUp(self):
        self.base = os.getenv("BASE_URL", "http://127.0.0.1")
        self.provisioner = f"{self.base}:{PROVISIONER_PORT}/provision"
        self.registry = f"{self.base}:{REGISTRY_PORT}"

    def test_entropy(self):
        self.assertIsNotNone(get_entropy(self.registry))

    def test_provision(self):
        res = provision(self.provisioner, get_entropy(self.registry), "secret")
        self.assertEqual(res.get("success"), True)
        self.assertIn("w3id", res)

    def test_bearer(self):
        self.assertIn("token", get_bearer_token(self.registry, "testplatform"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
