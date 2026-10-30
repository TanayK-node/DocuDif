import os
import json
import re
from typing import List, Optional
import sys
from pathlib import Path
import torch

sys.path.append(str(Path(__file__).resolve().parent.parent))
from schemas import LLMAnalysisOutput, RuleFlag
from llm_providers.base import BaseLLMProvider
from llm_providers.json_repair import extract_and_parse_json, validate_or_fallback_output
from llm_providers.fallback_provider import DeterministicFallbackProvider

DEFAULT_QWEN_MODEL = os.getenv("QWEN_MODEL_NAME", "Qwen/Qwen2.5-0.5B-Instruct")

PROMPT_TEMPLATE = """You are a document change analyzer. Output ONLY a valid JSON object.
Analyze the change between OLD and NEW text:

OLD: "{old_text}"
NEW: "{new_text}"
RULES: {rules}

Return ONLY this JSON schema:
{{
  "semantic_class": "material_change",
  "category": "{suggested_category}",
  "explanation": "Precise statement of what changed.",
  "implication": "Operational implication.",
  "confidence": 0.85,
  "requires_human_review": true
}}"""

class QwenProvider(BaseLLMProvider):
    def __init__(self, model_path: Optional[str] = None, lazy_load: bool = True):
        self.model_path = model_path or DEFAULT_QWEN_MODEL
        self.fallback = DeterministicFallbackProvider()
        self.model = None
        self.tokenizer = None
        self._load_attempted = False
        if not lazy_load:
            self._ensure_loaded()

    def get_provider_name(self) -> str:
        return f"Local Qwen ({self.model_path})"

    def _ensure_loaded(self) -> bool:
        if self._load_attempted:
            return self.model is not None

        self._load_attempted = True
        # Check if local offline execution is feasible
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            device = "cuda" if torch.cuda.is_available() else "cpu"
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            # If user has a local directory or wants to load
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch_dtype,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            if not torch.cuda.is_available():
                self.model.to("cpu")
            self.model.eval()
            return True
        except Exception as e:
            # Documented fallback if model weights not cached locally
            self.model = None
            self.tokenizer = None
            return False

    def analyze_change(
        self,
        old_text: str,
        new_text: str,
        rule_flags: List[RuleFlag],
        change_type: str = "modified"
    ) -> LLMAnalysisOutput:
        # If not loaded or model unavailable, use deterministic fallback
        if not self._ensure_loaded():
            out = self.fallback.analyze_change(old_text, new_text, rule_flags, change_type)
            out.llm_error = "Local Qwen weights not cached; automatically used deterministic rule engine."
            return out

        rules_str = ", ".join([f.description for f in rule_flags]) or "None"
        suggested_category = rule_flags[0].category if rule_flags else "Meaning or obligation changed"
        prompt = PROMPT_TEMPLATE.format(
            old_text=old_text,
            new_text=new_text,
            rules=rules_str,
            suggested_category=suggested_category
        )

        try:
            messages = [{"role": "user", "content": prompt}]
            if hasattr(self.tokenizer, "apply_chat_template"):
                inputs = self.tokenizer.apply_chat_template(
                    messages, tokenize=True, add_generation_prompt=True,
                    return_tensors="pt", return_dict=True
                )
            else:
                inputs = self.tokenizer(prompt, return_tensors="pt")

            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            with torch.inference_mode():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=220,
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id
                )
            gen_tokens = output[0][inputs["input_ids"].shape[1]:]
            raw_output = self.tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

            parsed = extract_and_parse_json(raw_output)
            if not parsed:
                # Retry repair pass or fallback
                fallback_res = self.fallback.analyze_change(old_text, new_text, rule_flags, change_type)
                fallback_res.llm_error = "Model generated invalid JSON; safely recovered with deterministic fallback."
                return fallback_res

            return validate_or_fallback_output(parsed, default_category=suggested_category)
        except Exception as e:
            fallback_res = self.fallback.analyze_change(old_text, new_text, rule_flags, change_type)
            fallback_res.llm_error = f"Qwen generation error: {str(e)[:180]}; recovered with fallback."
            return fallback_res

