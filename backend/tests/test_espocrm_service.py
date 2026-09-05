from __future__ import annotations

import base64
import unittest
from unittest.mock import Mock, patch

from app.services import espocrm_service


def mock_json_response(payload: dict, *, status_code: int = 200) -> Mock:
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    response.text = ""
    return response


class EspoCRMServiceTest(unittest.TestCase):
    def test_create_lead_uses_espo_authorization_token_flow(self) -> None:
        original_base_url = espocrm_service.settings.espocrm_base_url
        original_api_key = espocrm_service.settings.espocrm_api_key
        original_username = espocrm_service.settings.espocrm_username
        original_password = espocrm_service.settings.espocrm_password
        espocrm_service.settings.espocrm_base_url = "https://crm.example.test"
        espocrm_service.settings.espocrm_api_key = ""
        espocrm_service.settings.espocrm_username = "admin"
        espocrm_service.settings.espocrm_password = "password"
        try:
            with patch("app.services.espocrm_service.requests.get", return_value=mock_json_response({"token": "token-123"})) as mock_get:
                with patch("app.services.espocrm_service.requests.post", return_value=mock_json_response({"id": "lead-1"})) as mock_post:
                    response = espocrm_service.create_lead({"name": "Test Lead"})
        finally:
            espocrm_service.settings.espocrm_base_url = original_base_url
            espocrm_service.settings.espocrm_api_key = original_api_key
            espocrm_service.settings.espocrm_username = original_username
            espocrm_service.settings.espocrm_password = original_password

        self.assertEqual({"id": "lead-1"}, response)
        auth_request_headers = mock_get.call_args.kwargs["headers"]
        lead_request_headers = mock_post.call_args.kwargs["headers"]
        self.assertEqual(
            base64.b64encode(b"admin:password").decode("ascii"),
            auth_request_headers["Espo-Authorization"],
        )
        self.assertEqual(
            base64.b64encode(b"admin:token-123").decode("ascii"),
            lead_request_headers["Espo-Authorization"],
        )

    def test_list_contacts_reads_the_contact_collection(self) -> None:
        original_base_url = espocrm_service.settings.espocrm_base_url
        original_api_key = espocrm_service.settings.espocrm_api_key
        espocrm_service.settings.espocrm_base_url = "https://crm.example.test"
        espocrm_service.settings.espocrm_api_key = "api-key"
        try:
            response = mock_json_response({"list": [{"id": "contact-1", "name": "Jie Huang"}]})
            with patch("app.services.espocrm_service.requests.get", return_value=response) as mock_get:
                contacts = espocrm_service.list_contacts(limit=8)
        finally:
            espocrm_service.settings.espocrm_base_url = original_base_url
            espocrm_service.settings.espocrm_api_key = original_api_key

        self.assertEqual([{"id": "contact-1", "name": "Jie Huang"}], contacts)
        self.assertEqual("https://crm.example.test/api/v1/Contact", mock_get.call_args.args[0])
        self.assertEqual(8, mock_get.call_args.kwargs["params"]["maxSize"])
        self.assertEqual("api-key", mock_get.call_args.kwargs["headers"]["X-Api-Key"])


if __name__ == "__main__":
    unittest.main()
