import unittest
import os
import json
from unittest.mock import patch, mock_open

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.core.config import AppConfig, DEFAULT_CONFIG

class TestAppConfig(unittest.TestCase):
    @patch("src.core.config.os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"opacity": 50}')
    def test_load_existing_config(self, mock_file, mock_exists):
        mock_exists.return_value = True
        config = AppConfig.load()
        self.assertEqual(config["opacity"], 50)
        self.assertEqual(config["max_history_lines"], DEFAULT_CONFIG["max_history_lines"])

    @patch("src.core.config.os.path.exists")
    def test_load_non_existing_config(self, mock_exists):
        mock_exists.return_value = False
        config = AppConfig.load()
        self.assertEqual(config["opacity"], DEFAULT_CONFIG["opacity"])

    @patch("builtins.open", new_callable=mock_open)
    def test_save_config(self, mock_file):
        test_config = DEFAULT_CONFIG.copy()
        test_config["opacity"] = 40
        AppConfig.save(test_config)
        
        # Verify open was called
        mock_file.assert_called_once()
        
        # Verify write was called (json.dump calls write)
        handle = mock_file()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        written_json = json.loads(written_data)
        self.assertEqual(written_json["opacity"], 40)
        
    @patch("src.core.config.os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_corrupted_config(self, mock_file, mock_exists):
        mock_exists.return_value = True
        mock_file.return_value.read.side_effect = Exception("Simulated read error")
        config = AppConfig.load()
        # Should fallback to default config safely
        self.assertEqual(config["opacity"], DEFAULT_CONFIG["opacity"])

    @patch("builtins.open", new_callable=mock_open)
    def test_save_config_error(self, mock_file):
        mock_file.side_effect = Exception("Simulated write error")
        test_config = DEFAULT_CONFIG.copy()
        # Should not raise exception
        AppConfig.save(test_config)

if __name__ == '__main__':
    unittest.main()
