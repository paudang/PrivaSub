import os
import sys
import logging
import ctranslate2
from transformers import AutoTokenizer
from huggingface_hub import snapshot_download

logger = logging.getLogger("PrivaSub.Translator")

class OfflineTranslator:
    """
    Handles local English-to-Vietnamese translation using MarianMT via CTranslate2.
    Automatically downloads the model from Hugging Face on the first run.
    """
    def __init__(self, model_dir=None, device="cpu", compute_type="int8"):
        if model_dir is None:
            # Resolve path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.model_dir = os.path.join(base_dir, "models", "opus-mt-en-vi-ctranslate2")
        else:
            self.model_dir = model_dir

        self.device = device
        self.compute_type = compute_type
        self.translator = None
        self.tokenizer = None

        # Check and download model if necessary
        self._ensure_model_downloaded()
        
        # Load model and tokenizer
        self._load_model()

    def _ensure_model_downloaded(self):
        """Downloads the model from Hugging Face if not already present locally."""
        required_files = ["model.bin", "source.spm", "target.spm", "shared_vocabulary.json"]
        model_exists = os.path.exists(self.model_dir) and all(
            os.path.exists(os.path.join(self.model_dir, f)) for f in required_files
        )

        if not model_exists:
            logger.info(f"Model not found at {self.model_dir}. Downloading from Hugging Face...")
            os.makedirs(os.path.dirname(self.model_dir), exist_ok=True)
            try:
                snapshot_download(
                    repo_id="manancode/opus-mt-en-vi-ctranslate2-android",
                    local_dir=self.model_dir,
                    local_dir_use_symlinks=False
                )
                logger.info("Model downloaded successfully.")
            except Exception as e:
                logger.error(f"Failed to download translation model: {e}")
                raise RuntimeError(f"Translation model download failed: {e}")
        else:
            logger.info(f"Translation model found at {self.model_dir}.")

    def _load_model(self):
        """Initializes CTranslate2 translator and transformers tokenizer."""
        logger.info(f"Loading translation tokenizer from {self.model_dir}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
        
        logger.info(f"Loading CTranslate2 translator from {self.model_dir} (device={self.device}, compute_type={self.compute_type})...")
        self.translator = ctranslate2.Translator(
            self.model_dir,
            device=self.device,
            compute_type=self.compute_type
        )
        logger.info("Translation model loaded successfully.")

    def translate(self, text: str) -> str:
        """Translates a single English sentence to Vietnamese."""
        if not text or not text.strip():
            return ""

        try:
            # Tokenize text (AutoTokenizer automatically handles special tokens like </s>)
            tokens = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(text))
            
            # Translate tokens
            results = self.translator.translate_batch([tokens])
            target_tokens = results[0].hypotheses[0]
            
            # Decode back to string
            translated_text = self.tokenizer.decode(
                self.tokenizer.convert_tokens_to_ids(target_tokens),
                skip_special_tokens=True
            )
            return translated_text
        except Exception as e:
            logger.error(f"Translation failed for text '{text}': {e}")
            return text  # Fallback to original text on failure
