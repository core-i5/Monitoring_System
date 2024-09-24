import os
import unittest
from unittest.mock import patch
from queue import Queue
from app.todecode_monitor import ZipFileHandler

class TestZipFileHandler(unittest.TestCase):

    def setUp(self):
        self.output_folder = 'test_output'
        self.input_folder = 'test_input'
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.input_folder, exist_ok=True)
        self.processing_queue = Queue()
        self.handler = ZipFileHandler(self.output_folder, self.input_folder, self.processing_queue)

    def tearDown(self):
        # Remove files in output folder
        for file in os.listdir(self.output_folder):
            os.remove(os.path.join(self.output_folder, file))
        for file in os.listdir(self.input_folder):
            os.remove(os.path.join(self.input_folder, file))
        os.rmdir(self.output_folder)
        os.rmdir(self.input_folder)

    @patch('app.todecode_monitor.pyzipper.AESZipFile')
    def test_extract_and_filter(self, mock_zip):
        zip_file_path = 'test_file.zip'
        with open(zip_file_path, 'w') as f:
            f.write("Test content")

        self.handler.process_files()  # Simulate file processing

        self.assertTrue(os.path.exists(self.output_folder))
        os.remove(zip_file_path)

    def test_extract_password(self):
        zip_file_name = "Coding Assignment SE_2024_09_23_06_02_04_PM.zip"
        expected_password = "1695462004"  # This should match the epoch time for the timestamp
        actual_password = self.handler.extract_password(zip_file_name)
        self.assertEqual(actual_password, expected_password)

    def test_pii_filter(self):
        test_file = 'test_file.txt'
        with open(test_file, 'w') as f:
            f.write("Contact: john.doe@example.com on December 25, 1990.")

        self.handler.pii_filter(test_file)

        with open(os.path.join(self.output_folder, 'PII_filtered_test_file.txt'), 'r') as f:
            content = f.read()
            self.assertNotIn('john.doe@example.com', content)
            self.assertNotIn('December 25, 1990', content)

        os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
