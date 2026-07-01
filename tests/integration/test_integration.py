import os
import sys
import time
import unittest
import numpy as np
import wave
import re
import difflib
import io
from unittest.mock import patch, MagicMock

# Force UTF-8 encoding on Windows terminal output in-place safely
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from src.main import PrivaSubApp
from src.core.audio.file_extractor import extract_audio_to_wav
from src.core.config import AppConfig

class MockAudioCapture:
    def __init__(self, wav_filename, chunk_duration_ms=100):
        self.chunk_duration_ms = chunk_duration_ms
        self.selected_device_index = None
        self.device_index = 0
        self.running = False
        self.paused = False
        
        # Load the extracted wav file
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        wav_path = os.path.join(project_root, "tests", "videos", wav_filename)
        
        with wave.open(wav_path, "rb") as wf:
            params = wf.getparams()
            raw_data = wf.readframes(params.nframes)
            self.audio_data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
            
        # Force 500ms chunk duration to speed up integration testing (reduces Whisper calls by 5x)
        self.chunk_duration_ms = 500
        self.chunk_size = int(16000 * (self.chunk_duration_ms / 1000.0))
        self.current_idx = 0

    def get_available_devices(self):
        return [{'index': 0, 'name': 'Mock Loopback', 'is_loopback': True}]

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def get_audio_chunk(self):
        if self.paused or not self.running:
            return None
        if self.current_idx >= len(self.audio_data):
            return None
        chunk = self.audio_data[self.current_idx : self.current_idx + self.chunk_size]
        self.current_idx += self.chunk_size
        return chunk

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Prevent tk window from popping up physically
        import customtkinter as ctk
        cls.root = ctk.CTk()
        cls.root.withdraw()
        
        # Resolve paths
        cls.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cls.video_names = ["test-video.mp4", "test-video-02.mp4", "test-video-03.mp4"]
        
        # Extract audio to 16kHz mono WAV for all 3 videos, ensuring fresh files
        for name in cls.video_names:
            video_path = os.path.join(cls.project_root, "tests", "videos", name)
            wav_path = os.path.join(cls.project_root, "tests", "videos", name.replace(".mp4", ".wav"))
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
            print(f"[Test] Extracting audio from {video_path} to {wav_path}...")
            success = extract_audio_to_wav(video_path, wav_path)
            if not success:
                raise RuntimeError(f"Failed to extract audio from integration test video: {name}")

    @classmethod
    def tearDownClass(cls):
        # Destroy tk root
        cls.root.destroy()
        
        # Clean up the extracted WAV files to leave repository clean
        for name in cls.video_names:
            wav_path = os.path.join(cls.project_root, "tests", "videos", name.replace(".mp4", ".wav"))
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception as e:
                    print(f"[Test] Warning: failed to delete temp wav file {wav_path}: {e}")

    def assert_similarity(self, expected, actual, min_ratio, msg=""):
        """Normalizes and computes string similarity ratio using difflib.SequenceMatcher."""
        s1 = re.sub(r'[^\w\s]', '', expected.lower())
        s2 = re.sub(r'[^\w\s]', '', actual.lower())
        s1 = " ".join(s1.split())
        s2 = " ".join(s2.split())
        
        ratio = difflib.SequenceMatcher(None, s1, s2).ratio()
        self.assertTrue(
            ratio >= min_ratio,
            f"{msg} | Similarity ratio was {ratio:.2f}, expected >= {min_ratio:.2f}\n"
            f"Expected Reference: '{s1}'\n"
            f"Actual Text: '{s2}'"
        )

    def _run_integration_test_for_video(self, wav_filename, expected_en, expected_vi):
        # 1. Setup mock configuration
        with patch("src.main.AppConfig.load") as mock_config_load, \
             patch("src.main.pystray.Icon") as mock_pystray_icon_class, \
             patch("src.main.AudioCapture") as mock_audio_capture_class, \
             patch.object(PrivaSubApp, "hotkey_listener_loop", return_value=None):
             
            mock_config_load.return_value = {
                "source_language": "English (Translate Mode)",
                "target_language": "Vietnamese",
                "opacity": 80,
                "max_history_lines": 500,
                "auto_hide_timeout_s": 15,
                "audio_device_index": 0
            }
            
            mock_capture_instance = MockAudioCapture(wav_filename)
            mock_audio_capture_class.return_value = mock_capture_instance
            mock_pystray_icon_class.return_value = MagicMock()
            
            # 2. Start app
            app = PrivaSubApp()
            app.app.withdraw()
            
            # Verify initial welcome message
            initial_text = app.app.get_current_text()
            self.assertEqual(initial_text, "PrivaSub loaded. Listening to system audio...")
            
            # 3. Drive the Tkinter loop
            start_wait = time.time()
            max_wait_seconds = 120.0
            
            def check_progress():
                if mock_capture_instance.current_idx >= len(mock_capture_instance.audio_data):
                    app.app.after(3000, exit_main_loop)
                elif time.time() - start_wait > max_wait_seconds:
                    print("[Test] Integration test timed out waiting for audio processing.")
                    exit_main_loop()
                else:
                    app.app.after(100, check_progress)
                    
            def exit_main_loop():
                app.app.quit()
                
            app.app.after(100, check_progress)
            app.app.mainloop()
            
            # Cleanly stop processing thread
            app.running = False
            app.process_thread.join(timeout=5.0)
            
            final_content = app.app.get_current_text()
            print(f"=== INTEGRATION SUBTITLES FOR {wav_filename} ===")
            print(final_content)
            print("=================================================")
            
            # Assert initial welcome message was cleared
            self.assertNotIn("PrivaSub loaded. Listening to system audio...", final_content)
            
            # Parse English and Vietnamese text by retrieving their respective tags
            # to support line-wrapped text formatting.
            def get_text_by_tags(tag_names):
                text_widget = app.app.textbox._textbox
                accumulated = []
                for tag in tag_names:
                    ranges = text_widget.tag_ranges(tag)
                    for i in range(0, len(ranges), 2):
                        start = ranges[i]
                        end = ranges[i+1]
                        accumulated.append(text_widget.get(start, end))
                return " ".join(" ".join(accumulated).split())

            actual_en = get_text_by_tags(["en", "en_interim"])
            actual_vi = get_text_by_tags(["vi", "vi_interim"])
            
            # Perform similarity checks
            self.assert_similarity(expected_en, actual_en, 0.85, f"English transcription check for {wav_filename}")
            self.assert_similarity(expected_vi, actual_vi, 0.70, f"Vietnamese translation check for {wav_filename}")
            
            # Clean up UI
            app.on_exit(None, None)

    def test_video_01_live_captioning_and_translation(self):
        expected_en = (
            "mostly like what kind of words do i want to put in what kind of sound do i want "
            "i didnt realize walking into the studio was more about what knowing what i want what i really want "
            "all of it as well not just like working with someone who theres someone who gets you on the day "
            "and its like oh weve got a good vibe here this is a cool track its like no no no no no "
            "every step on this record and this record has to tell another part of your story and you write "
            "i think when people sound working really hard would very hard work is a distraction from selfwork mmhmm so"
        )
        expected_vi = (
            "hầu hết là kiểu như tôi muốn đưa vào những từ như thế nào tôi muốn âm thanh như thế nào "
            "tôi không nhận ra bước vào phòng thu là video nói về việc biết tôi muốn gì tôi thực sự muốn gì "
            "tất cả cũng vậy không chỉ làm việc với người có ai đó có thể làm cho bạn ngày và nó giống như ồ chúng ta "
            "có một cảm xúc tốt ở đây đây là một bài hát tuyệt vời nó giống như không không không không không mỗi bước "
            "trên đĩa này và như raycote phải kể lại một phần khác của câu chuyện của bạn và anh nói đúng tôi nghĩ khi "
            "mọi người nghe có vẻ làm việc chăm chỉ họ sẽ"
        )
        self._run_integration_test_for_video("test-video.wav", expected_en, expected_vi)

    def test_video_02_live_captioning_and_translation(self):
        expected_en = (
            "special guys ive ever had oh well stop stop i told you i thought sick stop its just so in my ears "
            "tonight we have one of the most special guests ive ever had rosie pop singer songwriter superstar "
            "her new single number one girl is out everywhere now as well as the number one smash head oppa te with "
            "bruno mars her debut album rote the album rosie is out december 6th"
        )
        expected_vi = (
            "những người đặc biệt tôi đã từng có oh chào được rồi dừng lại ngừng đi tôi đã nói tôi nghĩ mình bị bệnh "
            "đừng đi nó chỉ là như vậy trong tai của tôi tối nay chúng ta có một trong những những khách mà tôi từng có "
            "rosie ca sĩ nhạc pop nhà soạn nhạc siêu sao cô gái mới của cô ấy là hiện nay anh ấy đang ở khắp mọi nơi "
            "cũng như là người đứng đầu với bruno mars album ra mắt của cô ấy rote"
        )
        self._run_integration_test_for_video("test-video-02.wav", expected_en, expected_vi)

    def test_video_03_live_captioning_and_translation(self):
        expected_en = (
            "i just love the lyrics i think its like some of my favorite lyrics ive ever written why wasnt in the "
            "three that you mentioned because nowhere near my mouth streamed which is totally fine what do you think "
            "it is who cares great honestly but i love singing it on tour as well its like one of my favorite songs "
            "to sing live its just super fun i have this other one called spinit its called spinning that comes to "
            "mind that i love very dearly why do you love them again just i think lyrically like i think that those "
            "songs are these are our songs that had no one"
        )
        expected_vi = (
            "tôi thích lời bài hát tôi nghĩ đó giống như một số lời bài hát yêu thích của tôi mà tôi từng viết "
            "tại sao không có trong ba người mà anh đề cập bởi vì miệng tôi cũng không chảy điều đó hoàn toàn ổn anh nghĩ "
            "là cái gì ai quan tâm tốt lắm thật sự nhưng tôi cũng thích hát khi đi lưu diễn nó giống như một trong những "
            "bài hát yêu thích của tôi để hát trực tiếp thật vui đấy tôi còn có cái tên khác gọi là spinit nó được gọi là "
            "quay mà tôi nhớ rằng tôi rất yêu nó tại sao anh lại yêu họ một lần nữa tôi nghĩ theo cách lyrical tôi nghĩ "
            "những bài hát đó là những bài hát này là bài hát của chúng tôi mà không có ai"
        )
        self._run_integration_test_for_video("test-video-03.wav", expected_en, expected_vi)

if __name__ == "__main__":
    unittest.main()
