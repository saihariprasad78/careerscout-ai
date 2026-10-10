import os
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException

import main


class CareerScoutTests(unittest.TestCase):
    def test_health_reports_missing_key_without_exposing_value(self):
        with patch.dict(os.environ, {}, clear=True):
            response = main.health()
        self.assertEqual(response, {"status": "ok", "serpapi_configured": False})

    def test_jobs_requires_configured_key(self):
        with patch.dict(os.environ, {"SERPAPI_KEY": "your_serpapi_key_here"}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                main.search_jobs()
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("backend/.env", raised.exception.detail)

    @patch.object(main.requests, "get")
    def test_search_uses_google_jobs_and_returns_evidence_and_caution(self, get):
        get.return_value = Mock(status_code=200)
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"search_metadata": {"status": "Success"}, "jobs_results": [{
            "title": "Junior Analyst", "company_name": "Example Ltd", "location": "Pune, India",
            "description": "Pay registration fee to apply on WhatsApp", "share_link": "https://www.google.com/search?q=jobs",
        }]}
        with patch.dict(os.environ, {"SERPAPI_KEY": "test-key"}, clear=True):
            response = main.search_jobs(role="Analyst", location="Pune", limit=10)
        self.assertEqual(response["count"], 1)
        job = response["jobs"][0]
        self.assertEqual(job["evidence_url"], "https://www.google.com/search?q=jobs")
        self.assertEqual(job["risk"]["level"], "caution")
        self.assertTrue(any("fee" in signal for signal in job["risk"]["signals"]))
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["engine"], "google_jobs")
        self.assertEqual(params["gl"], "in")
        self.assertEqual(params["api_key"], "test-key")

    @patch.object(main.requests, "get")
    def test_serpapi_error_is_sanitized(self, get):
        get.return_value = Mock(status_code=200)
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"error": "private provider details"}
        with patch.dict(os.environ, {"SERPAPI_KEY": "test-key"}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                main.search_jobs(limit=10)
        self.assertEqual(raised.exception.status_code, 502)
        self.assertNotIn("private provider details", raised.exception.detail)

    def test_home_serves_frontend(self):
        response = main.home()
        self.assertEqual(response.path.name, "index.html")

    @patch.object(main.requests, "get")
    def test_dossier_returns_real_search_source_and_explains_limits(self, get):
        get.return_value = Mock(status_code=200)
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"organic_results": [{
            "title": "Careers at Example Ltd", "source": "example.com",
            "link": "https://example.com/careers", "snippet": "Junior Analyst opening in Pune.",
        }]}
        with patch.dict(os.environ, {"SERPAPI_KEY": "test-key"}, clear=True):
            result = main.investigate_job(company="Example Ltd", title="Junior Analyst", location="Pune")
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["engine"], "google")
        self.assertIn("Example Ltd", params["q"])
        self.assertEqual(params["gl"], "in")
        self.assertEqual(result["result_count"], 1)
        self.assertEqual(result["sources"][0]["url"], "https://example.com/careers")
        self.assertEqual(result["sources"][0]["snippet"], "Junior Analyst opening in Pune.")
        self.assertTrue(result["unknowns"])
        self.assertTrue(result["before_apply"])
        self.assertIn("not proof", result["cautions"][0])

    @patch.object(main.requests, "get")
    def test_dossier_missing_sources_are_not_a_fraud_claim(self, get):
        get.return_value = Mock(status_code=200)
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"organic_results": []}
        with patch.dict(os.environ, {"SERPAPI_KEY": "test-key"}, clear=True):
            result = main.investigate_job(company="Example Ltd", title="Analyst", location="Pune")
        self.assertEqual(result["sources"], [])
        self.assertIn("not evidence", result["cautions"][0])
        self.assertNotIn("fraud", result["cautions"][0].lower())

    @patch.object(main.requests, "get")
    def test_dossier_provider_error_is_sanitized(self, get):
        get.return_value = Mock(status_code=200)
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"error": "private provider error and key details"}
        with patch.dict(os.environ, {"SERPAPI_KEY": "test-key"}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                main.investigate_job(company="Example Ltd", title="Analyst", location="Pune")
        self.assertEqual(raised.exception.status_code, 502)
        self.assertNotIn("private provider error", raised.exception.detail)
        self.assertNotIn("test-key", raised.exception.detail)

    @patch.object(main.requests, "get")
    def test_dossier_api_timeout_is_reported_without_details(self, get):
        get.side_effect = main.requests.Timeout("private URL and key details")
        with patch.dict(os.environ, {"SERPAPI_KEY": "test-key"}, clear=True):
            with self.assertRaises(HTTPException) as raised:
                main.investigate_job(company="Example Ltd", title="Analyst", location="Pune")
        self.assertEqual(raised.exception.status_code, 504)
        self.assertNotIn("private URL", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
