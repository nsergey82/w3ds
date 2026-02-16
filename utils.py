import os
from typing import Dict

from gql import Client, gql, transport
from gql.transport.aiohttp import AIOHTTPTransport

PUBLIC_PROVISIONER_URL = os.getenv(
    "PUBLIC_PROVISIONER_URL", "http://64.227.64.55:4000/graphql"
)


def _start_client(ename: str, token: str) -> Client:
    transport = AIOHTTPTransport(
        url=PUBLIC_PROVISIONER_URL,  # strictly we should ask the registry for ename's ip
        headers={"X-ENAME": ename, "Authorization": f"Bearer {token}"},
    )
    return Client(transport=transport)


def _build_envelope(envelope):
    return f'''{envelope[0]}: "{envelope[1]}"'''


def envelope_to_py(metaenvelope: Dict):
    envelopes = metaenvelope.get("envelopes", [])
    return {en["ontology"]: en["value"] for en in envelopes}


class VaultIO:
    def __init__(self, token: str, ename: str):
        self.token = token
        self.ename = ename

    def get_metaenv_ids(self, ontology: str):
        client = _start_client(self.ename, self.token)
        query = gql(
            """
            query Q ($ontology: ID!){
                metaEnvelopes(filter: {ontologyId: $ontology}) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
            """
        )
        query.variable_values = {"ontology": ontology}
        result = client.execute(query)
        edges = result.get("metaEnvelopes", {"edges": []})["edges"]
        return [edge["node"]["id"] for edge in edges]

    def get_envelopes_for_ontology(self, ontology: str):
        client = _start_client(self.ename, self.token)
        query = gql(
            """
            query Q ($ontology: ID!){
                metaEnvelopes(filter: {ontologyId: $ontology}) {
                    edges {
                        node {
                            id
                            envelopes {
                                ontology
                                value
                            }
                        }
                    }
                }
            }
            """
        )
        query.variable_values = {"ontology": ontology}
        result = client.execute(query)
        return [
            edge["node"] for edge in result.get("metaEnvelopes", {"edges": []})["edges"]
        ]

    def get_metaenv_values(self, mid: str) -> Dict[str, str]:
        client = _start_client(self.ename, self.token)
        query = gql(
            """
            query Q ($mid: ID!) {
            metaEnvelope(id: $mid) {
                id
                ontology
                envelopes {
                    ontology
                    value
                }
                }
            }
            """
        )
        query.variable_values = {"mid": mid}
        result = client.execute(query).get("metaEnvelope", {"envelopes": []})[
            "envelopes"
        ]
        return {envelope["ontology"]: envelope["value"] for envelope in result}

    def delete_metaenv(self, mid: str):
        client = _start_client(self.ename, self.token)
        mutation = gql(
            """
            mutation M($mid: ID!) {
                removeMetaEnvelope(id: $mid)
            }
            """
        )
        mutation.variable_values = {"mid": mid}
        try:
            rc = client.execute(mutation)
        except transport.exceptions.TransportQueryError as e:
            print("error deleting:", e)
            return None
        return rc.get("errors", None)

    def store_envelopes(self, metaontology: str, envelopes: Dict[str, str]):
        # TODO: use variables instead of injection fro payload
        client = _start_client(self.ename, self.token)
        payload = ",".join([_build_envelope(p) for p in envelopes.items()])
        mutation = gql(
            f"""
                mutation M($ontology: String!){{
                createMetaEnvelope(input: {{
                        ontology: $ontology,
                        payload: {{
                            {payload}
                        }},
                        acl: ["*"]}}) {{
                    metaEnvelope {{
                        id
                    }}
                }}
                }}
            """
        )
        mutation.variable_values = {"ontology": metaontology}
        rc = client.execute(mutation)
        return rc.get("errors", None)
