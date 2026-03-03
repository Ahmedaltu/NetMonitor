import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class TestNetMonitorDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        cls.driver = webdriver.Chrome(options=chrome_options)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_operational_status_panel(self):
        self.driver.get('http://localhost:5174/')
        time.sleep(2)  # Wait for page to load
        root = self.driver.find_element(By.ID, 'root')
        self.assertIsNotNone(root)
        # Check for agent identifier
        agent = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Agent')]")
        self.assertIsNotNone(agent)
        # Check for health state
        health = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Health')]")
        self.assertIsNotNone(health)
        # Check for color indicator
        indicator = self.driver.find_element(By.CSS_SELECTOR, 'span.w-4.h-4.rounded-full')
        self.assertIsNotNone(indicator)
        # Check for time window selector
        select = self.driver.find_element(By.TAG_NAME, 'select')
        self.assertIsNotNone(select)

if __name__ == '__main__':
    unittest.main()
