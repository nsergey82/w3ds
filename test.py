import unittest
import os
from utils import VaultIO, envelope_to_py

# this is integration test, it needs a proper graphql endpoint
# override utils.PUBLIC_PROVISIONER_URL or set env. variable

# also, the tests run in order


class TestEnvelopes(unittest.TestCase):
    def setUp(self):
        ename = os.getenv("ENAME", "@82f7a77a-f03a-52aa-88fc-1b1e488ad498")
        token = os.getenv("PP_JWT_TOKEN", "secret")
        self.vio = VaultIO(token, ename)
        self.ontology = "TEST_ONTOLOGY" + str(os.getpid())
        self.src = {"keyInt": 1, "keyStr": "value"}
        self.mid = self.vio.store_envelopes(self.ontology, self.src)

    def tearDown(self):
        self.vio.delete_metaenv(self.mid)

    def test_creating(self):
        self.assertIsNotNone(self.mid)

    def test_getting_ids(self):
        ids = self.vio.get_metaenv_ids(self.ontology)
        self.assertIn(self.mid, ids)

    def test_getting_by_id(self):
        values = self.vio.get_metaenv_values(self.mid)
        self.assertDictEqual(self.src, values)

    def test_getting_envelopes(self):
        menvs = self.vio.get_envelopes_for_ontology(self.ontology)
        self.assertGreaterEqual(len(menvs), 1)
        menv = menvs[0]

        self.assertEqual(menv.get("id", ""), self.mid)
        self.assertEqual(len(self.src.keys()), len(menv.get("envelopes", [])))

        dst = envelope_to_py(menv)
        self.assertDictEqual(self.src, dst)

    def test_removing_envelopes(self):
        for mid in self.vio.get_metaenv_ids(self.ontology):
            rc = self.vio.delete_metaenv(mid)
            self.assertEqual(rc, mid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
