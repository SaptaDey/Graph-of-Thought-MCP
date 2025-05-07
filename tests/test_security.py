import unittest
import subprocess
import os

class TestSecurity(unittest.TestCase):

    def test_bandit_security(self):
        """Test for common security vulnerabilities using Bandit."""
        result = subprocess.run(['bandit', '-r', 'src'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Bandit found security issues:\n{result.stdout}")

    def test_sonarqube_analysis(self):
        """Test for code quality and security issues using SonarQube."""
        # Assuming SonarQube is set up and running locally
        result = subprocess.run(['sonar-scanner'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"SonarQube found issues:\n{result.stdout}")

    def test_owasp_zap_analysis(self):
        """Test for security vulnerabilities using OWASP ZAP."""
        # Assuming OWASP ZAP is set up and running locally
        result = subprocess.run(['zap-cli', 'quick-scan', 'http://localhost:8082'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"OWASP ZAP found issues:\n{result.stdout}")

    def test_security_analysis_output(self):
        """Validate the output of the security analysis tools."""
        # Check Bandit output
        bandit_result = subprocess.run(['bandit', '-r', 'src'], capture_output=True, text=True)
        self.assertIn('No issues identified.', bandit_result.stdout, f"Unexpected Bandit output:\n{bandit_result.stdout}")

        # Check SonarQube output
        sonar_result = subprocess.run(['sonar-scanner'], capture_output=True, text=True)
        self.assertIn('EXECUTION SUCCESS', sonar_result.stdout, f"Unexpected SonarQube output:\n{sonar_result.stdout}")

        # Check OWASP ZAP output
        zap_result = subprocess.run(['zap-cli', 'quick-scan', 'http://localhost:8082'], capture_output=True, text=True)
        self.assertIn('PASS', zap_result.stdout, f"Unexpected OWASP ZAP output:\n{zap_result.stdout}")

if __name__ == '__main__':
    unittest.main()
