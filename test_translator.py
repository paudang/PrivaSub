import sys
import io
import logging

# Force UTF-8 output on Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from src.translator import OfflineTranslator

def main():
    print("=== Testing OfflineTranslator ===")
    try:
        translator = OfflineTranslator()
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)
    
    test_cases = [
        "Welcome to PrivaSub!",
        "Hello, how can I help you today?",
        "This software provides offline English subtitles.",
        "Speech recognition and machine translation run 100% offline."
    ]
    
    print("\n=== Running translations ===")
    for text in test_cases:
        translated = translator.translate(text)
        print(f"EN: {text}")
        print(f"VI: {translated}")
        print("-" * 40)

if __name__ == "__main__":
    main()
