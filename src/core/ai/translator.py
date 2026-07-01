import os
import sys
import logging
import ctranslate2
from transformers import AutoTokenizer
from huggingface_hub import snapshot_download

logger = logging.getLogger("PrivaSub.Translator")

NLLB_LANGUAGE_CODES = {
    "English": "eng_Latn",
    "Vietnamese": "vie_Latn",
    "Japanese": "jpn_Jpan",
    "Chinese (Simplified)": "zho_Hans",
    "Chinese (Traditional)": "zho_Hant",
    "Korean": "kor_Hang",
    "Spanish": "spa_Latn",
    "French": "fra_Latn",
    "German": "deu_Latn",
    "Russian": "rus_Cyrl",
    "Thai": "tha_Thai"
}

def get_nllb_code(lang_str: str, default: str = "vie_Latn") -> str:
    if not lang_str:
        return default
    if lang_str == "en":
        return "eng_Latn"
    if lang_str == "vi":
        return "vie_Latn"
    if lang_str in NLLB_LANGUAGE_CODES:
        return NLLB_LANGUAGE_CODES[lang_str]
    if "_" in lang_str and len(lang_str) == 8:
        return lang_str
    return default

class OfflineTranslator:
    """
    Handles local English-to-Multilingual translation using Meta NLLB-200 via CTranslate2.
    Automatically downloads the model from Hugging Face on the first run.
    """
    def __init__(self, model_dir=None, device="cpu", compute_type="int8", source_lang="en", target_lang="vi"):
        self.device = device
        self.compute_type = compute_type
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = None
        self.tokenizer = None
        
        self.model_dir = self._resolve_model_dir(model_dir)

        # Check and download model if necessary
        self._ensure_model_downloaded()
        
        # Load model and tokenizer
        self._load_model()

    def _resolve_model_dir(self, custom_dir=None):
        if custom_dir:
            return custom_dir
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # NLLB is a single multilingual model capable of both en->vi and vi->en perfectly
        return os.path.join(base_dir, "models", "nllb-200-distilled-600M-ct2-int8")

    def _ensure_model_downloaded(self):
        """Downloads the NLLB CTranslate2 model from Hugging Face if not already present locally."""
        required_files = ["model.bin", "shared_vocabulary.json"]
        model_exists = os.path.exists(self.model_dir) and all(
            os.path.exists(os.path.join(self.model_dir, f)) for f in required_files
        )

        if not model_exists:
            logger.info(f"Model not found at {self.model_dir}. Downloading NLLB-200 from Hugging Face...")
            os.makedirs(os.path.dirname(self.model_dir), exist_ok=True)
            try:
                snapshot_download(
                    repo_id="JustFrederik/nllb-200-distilled-600M-ct2-int8",
                    local_dir=self.model_dir,
                    local_dir_use_symlinks=False
                )
                logger.info("NLLB Model downloaded successfully.")
            except Exception as e:
                logger.error(f"Failed to download NLLB translation model: {e}")
                raise RuntimeError(f"Translation model download failed: {e}")
        else:
            logger.info(f"NLLB translation model found at {self.model_dir}.")

    def _load_model(self):
        """Initializes CTranslate2 translator and transformers tokenizer."""
        src_code = get_nllb_code(self.source_lang, default="eng_Latn")
        logger.info(f"Loading translation tokenizer (src_lang={src_code})...")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M", src_lang=src_code, local_files_only=True)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M", src_lang=src_code, local_files_only=False)
        
        logger.info(f"Loading CTranslate2 translator from {self.model_dir} (device={self.device}, compute_type={self.compute_type})...")
        self.translator = ctranslate2.Translator(
            self.model_dir,
            device=self.device,
            compute_type=self.compute_type
        )
        logger.info("NLLB Translation model loaded successfully.")

    def translate(self, text: str) -> str:
        """Translates text between English and target language, splitting into sentences to preserve full content."""
        if not text or not text.strip():
            return ""

        if not self.translator or not self.tokenizer:
            logger.warning("Translator model not initialized. Skipping translation.")
            return text

        import re
        # Split text into sentences using simple regex (split on ., ?, ! followed by space)
        sentences = re.split(r'(?<=[.?!])\s+', text.strip())
        
        translated_sentences = []
        for sentence in sentences:
            if not sentence.strip():
                continue
            translated_sentences.append(self._translate_single_sentence(sentence))
            
        return " ".join(translated_sentences)

    def _translate_single_sentence(self, text: str) -> str:
        """Translates a single sentence using the loaded model."""
        try:
            # Prepare target language prefix
            tgt_code = get_nllb_code(self.target_lang, default="vie_Latn")
            
            # Tokenize input text
            input_ids = self.tokenizer.encode(text)
            input_tokens = self.tokenizer.convert_ids_to_tokens(input_ids)
            
            # Perform CTranslate2 batch translation
            results = self.translator.translate_batch([input_tokens], target_prefix=[[tgt_code]])
            output_tokens = results[0].hypotheses[0]
            
            # Strip target prefix from output tokens if present
            if output_tokens and output_tokens[0] == tgt_code:
                output_tokens = output_tokens[1:]
                
            translated_text = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(output_tokens), skip_special_tokens=True)
            
            # Post-processing: maintain natural ending punctuation matching source
            translated_text = translated_text.strip()
            if text.endswith('.') and not translated_text.endswith('.'):
                translated_text += '.'
            elif not text.endswith('.') and translated_text.endswith('.'):
                translated_text = translated_text[:-1]

            return translated_text
        except Exception as e:
            logger.error(f"Single sentence translation failed for '{text}': {e}")
            return text

    def set_translation_direction(self, source_lang, target_lang):
        """Dynamically switches translation direction."""
        if source_lang == self.source_lang and target_lang == self.target_lang:
            return
            
        logger.info(f"Switching translation direction to {source_lang} -> {target_lang}")
        self.source_lang = source_lang
        self.target_lang = target_lang
        
        # Update tokenizer source language instantly without reloading CTranslate2 weights
        if self.tokenizer:
            src_code = get_nllb_code(self.source_lang, default="eng_Latn")
            self.tokenizer.src_lang = src_code
