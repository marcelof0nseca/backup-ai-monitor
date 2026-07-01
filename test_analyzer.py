import unittest

from analyzer import classify_logs, parse_log


class AnalyzerTests(unittest.TestCase):
    def test_parse_login_failed_log(self):
        parsed = parse_log(
            "[2026-06-25 10:00:00] "
            "LOGIN_FAILED user=root ip=192.168.0.25"
        )

        self.assertEqual(parsed["event"], "LOGIN_FAILED")
        self.assertEqual(parsed["user"], "root")
        self.assertEqual(parsed["ip"], "192.168.0.25")

    def test_detects_brute_force_from_same_ip(self):
        logs = [
            "[2026-06-25 10:00:00] "
            "LOGIN_FAILED user=root ip=192.168.0.25",
            "[2026-06-25 10:00:20] "
            "LOGIN_FAILED user=root ip=192.168.0.25",
            "[2026-06-25 10:00:40] "
            "LOGIN_FAILED user=root ip=192.168.0.25",
        ]

        result = classify_logs(logs, logs)

        self.assertEqual(result["severity"], "CRITICAL")
        self.assertEqual(
            result["diagnosis"],
            "Possivel tentativa de brute force",
        )

    def test_does_not_mix_different_ips(self):
        logs = [
            "[2026-06-25 10:00:00] "
            "LOGIN_FAILED user=root ip=192.168.0.25",
            "[2026-06-25 10:00:20] "
            "LOGIN_FAILED user=admin ip=10.0.0.8",
            "[2026-06-25 10:00:40] "
            "LOGIN_FAILED user=backup ip=45.66.12.9",
        ]

        result = classify_logs(logs, logs)

        self.assertEqual(result["severity"], "WARNING")

    def test_unauthorized_access_is_high_severity(self):
        logs = [
            "[2026-06-25 10:00:00] "
            "UNAUTHORIZED_ACCESS /admin-panel"
        ]

        result = classify_logs(logs, logs)

        self.assertEqual(result["severity"], "HIGH")


if __name__ == "__main__":
    unittest.main()
