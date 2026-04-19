"""Local Hugging Face generation client with an OpenAI Responses-like surface."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any


@dataclass(slots=True)
class LocalGenerationConfig:
    model_name_or_path: str
    max_input_tokens: int = 4096
    trust_remote_code: bool = False


class LocalTransformersResponsesAPI:
    def __init__(self, config: LocalGenerationConfig) -> None:
        self.config = config
        self._tokenizer = None
        self._model = None
        self._runtime_device = "cpu"
        self._input_device = "cpu"

    def _resolve_runtime(self):
        import torch

        if torch.cuda.is_available():
            return {
                "runtime_device": "cuda",
                "input_device": "cuda:0",
                "supports_sampling": True,
                "model_kwargs": {
                    "dtype": torch.bfloat16,
                    "device_map": "auto",
                },
            }
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return {
                "runtime_device": "mps",
                "input_device": "mps",
                "supports_sampling": False,
                "model_kwargs": {
                    "dtype": torch.float16,
                    "low_cpu_mem_usage": True,
                },
            }
        return {
            "runtime_device": "cpu",
            "input_device": "cpu",
            "supports_sampling": False,
            "model_kwargs": {
                "dtype": torch.float32,
                "low_cpu_mem_usage": True,
            },
        }

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer

        runtime = self._resolve_runtime()
        self._runtime_device = str(runtime["runtime_device"])
        self._input_device = str(runtime["input_device"])
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            use_fast=True,
            trust_remote_code=self.config.trust_remote_code,
        )
        if self._tokenizer.pad_token is None and self._tokenizer.eos_token is not None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        self._model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=self.config.trust_remote_code,
            **runtime["model_kwargs"],
        )
        if self._runtime_device in {"mps", "cpu"}:
            self._model.to(self._runtime_device)
        self._model.eval()

    def create(
        self,
        *,
        model: str,
        temperature: float,
        max_output_tokens: int,
        input: str,
        **_: Any,
    ) -> SimpleNamespace:
        import torch

        self._ensure_loaded()
        tokenizer = self._tokenizer
        local_model = self._model
        encoded = tokenizer(
            str(input),
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_input_tokens,
        )
        encoded = {key: value.to(self._input_device) for key, value in encoded.items()}
        do_sample = float(temperature) > 0 and self._runtime_device == "cuda"
        generation_kwargs = {
            "max_new_tokens": int(max_output_tokens),
            "do_sample": do_sample,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "use_cache": True,
            "remove_invalid_values": True,
        }
        if do_sample:
            generation_kwargs["temperature"] = float(temperature)
            generation_kwargs["top_p"] = 0.9
        with torch.no_grad():
            output = local_model.generate(**encoded, **generation_kwargs)
        prompt_length = encoded["input_ids"].shape[1]
        generated_tokens = output[0][prompt_length:]
        output_text = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        return SimpleNamespace(output_text=output_text, model=model)


class LocalTransformersClient:
    def __init__(
        self,
        model_name_or_path: str,
        *,
        max_input_tokens: int = 4096,
        trust_remote_code: bool = False,
    ) -> None:
        self.responses = LocalTransformersResponsesAPI(
            LocalGenerationConfig(
                model_name_or_path=model_name_or_path,
                max_input_tokens=max_input_tokens,
                trust_remote_code=trust_remote_code,
            )
        )
