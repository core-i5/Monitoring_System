import os
import time
import unittest
from unittest.mock import patch, MagicMock
from queue import Queue
from threading import Thread

from app.folder_monitor import start_folder_monitor, TxtFileHandler

class TestTxtFileHandler(unittest.TestCase):

    def setUp(self):
        self.output_folder = 'test_output'
        os.makedirs(self.output_folder, exist_ok=True)
        self.processing_queue = Queue()
        self.handler = TxtFileHandler(self.output_folder, self.processing_queue)

    def tearDown(self):
        # Remove files in output folder
        for file in os.listdir(self.output_folder):
            os.remove(os.path.join(self.output_folder, file))
        os.rmdir(self.output_folder)

    @patch('app.folder_monitor.pyzipper.AESZipFile')
    def test_create_zip(self, mock_zip):
        test_file = 'test_file.txt'
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        self.handler.create_zip(test_file)

        expected_zip_name = f"test_file_{time.strftime('%Y_%m_%d_%I_%M_%S_%p', time.gmtime())}.zip"
        zip_path = os.path.join(self.output_folder, expected_zip_name)

        self.assertTrue(os.path.exists(zip_path))
        os.remove(test_file)
        os.remove(zip_path)

    def test_on_created(self):
        event = MagicMock()
        event.src_path = 'test_file.txt'
        self.handler.on_created(event)

        self.assertEqual(self.processing_queue.qsize(), 1)

    def test_process_files(self):
        test_file = 'test_file.txt'
        with open(test_file, 'w') as f:
            f.write("Test content")

        self.processing_queue.put(test_file)
        processing_thread = Thread(target=self.handler.process_files)
        processing_thread.start()

        time.sleep(1)  # Allow processing to occur
        self.assertEqual(self.processing_queue.qsize(), 0)

        os.remove(test_file)

    @patch('app.folder_monitor.Observer')
    @patch('app.folder_monitor.TxtFileHandler')
    def test_start_folder_monitor(self, MockTxtFileHandler, MockObserver):
        mock_observer = MockObserver.return_value
        mock_handler = MockTxtFileHandler.return_value
        
        input_folder = 'test_input_folder'
        os.makedirs(input_folder, exist_ok=True)

        try:
            start_folder_monitor(input_folder, self.output_folder, self.processing_queue)

            MockObserver.assert_called_once_with()
            MockTxtFileHandler.assert_called_once_with(self.output_folder, self.processing_queue)
            mock_observer.schedule.assert_called_once_with(mock_handler, input_folder, recursive=True)
            mock_observer.start.assert_called_once()
        finally:
            # Clean up input folder
            if os.path.exists(input_folder):
                os.rmdir(input_folder)

if __name__ == '__main__':
    unittest.main()
