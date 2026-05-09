"""
Equipment — The tools your agent uses.

Equipment is the data + tools layer. Models, APIs, hardware.
Each piece of equipment is independent and swappable.

Layers (from JC1's four-layer architecture):
  Vessel   → runtime (this SDK + PLATO server)
  Equipment → data + tools (THIS FILE)
  Agent    → reasoning (armor + session)
  Skills   → behavior (skill functions)
"""

import json
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError


class Equipment:
    """Base class for all equipment."""
    name: str = "base"
    description: str = "Base equipment"

    def setup(self, agent):
        """Called when equipment is attached to an agent."""
        self.agent = agent

    def teardown(self):
        """Called when equipment is removed."""
        pass

    def info(self) -> dict:
        return {"name": self.name, "description": self.description}


class RemoteModel(Equipment):
    """A remote API model (OpenAI, Anthropic, Groq, DeepSeek, etc.).

    Usage:
        model = RemoteModel(
            provider="groq",
            model="llama-3.3-70b-versatile",
            api_key="gsk_...",
            base_url="https://api.groq.com/openai/v1",
        )
    """

    def __init__(self, provider: str, model: str, api_key: str = None,
                 base_url: str = None, temperature: float = 0.7,
                 max_tokens: int = 2000):
        self.name = f"remote-{provider}"
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or self._default_url(provider)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _default_url(self, provider: str) -> str:
        urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "deepseek": "https://api.deepseek.com",
            "moonshot": "https://api.moonshot.ai/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "siliconflow": "https://api.siliconflow.com/v1",
        }
        return urls.get(provider, "")

    def generate(self, system_prompt: str, messages: list,
                 temperature: float = None) -> str:
        """Generate a response from the model."""
        temp = temperature or self.temperature
        all_messages = [{"role": "system", "content": system_prompt}] + messages

        payload = {
            "model": self.model,
            "messages": all_messages,
            "temperature": temp,
            "max_tokens": self.max_tokens,
        }

        url = f"{self.base_url}/chat/completions"
        req = Request(url, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "cocapn-plato-sdk/1.0")
        if self.api_key:
            if self.provider == "anthropic":
                req.add_header("x-api-key", self.api_key)
                req.add_header("anthropic-version", "2023-06-01")
            else:
                req.add_header("Authorization", f"Bearer {self.api_key}")

        resp = urlopen(req, json.dumps(payload).encode(), timeout=120)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    def info(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
        }


class LocalModel(Equipment):
    """A local model via PyTorch/transformers.

    Usage:
        model = LocalModel("meta-llama/Llama-3.1-8B-Instruct")
        model.load()  # downloads and caches
        response = model.generate("system prompt", [{"role": "user", "content": "hello"}])
    """

    def __init__(self, model_name: str, device: str = "auto",
                 max_tokens: int = 2000, temperature: float = 0.7):
        self.name = f"local-{model_name.split('/')[-1]}"
        self.model_name = model_name
        self.device = device
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._model = None
        self._tokenizer = None

    def load(self):
        """Load the model and tokenizer."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
        except ImportError:
            raise ImportError("pip install torch transformers to use LocalModel")

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=self.device,
        )

    def generate(self, system_prompt: str, messages: list,
                 temperature: float = None) -> str:
        """Generate a response from the local model."""
        if self._model is None:
            self.load()

        temp = temperature or self.temperature
        text = system_prompt + "\n\n"
        for msg in messages:
            text += f"{msg['role']}: {msg['content']}\n"
        text += "assistant: "

        inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)
        outputs = self._model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=temp,
            do_sample=True,
        )
        response = self._tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:],
                                           skip_special_tokens=True)
        return response.strip()

    def info(self) -> dict:
        return {
            "name": self.name,
            "model": self.model_name,
            "device": self.device,
            "loaded": self._model is not None,
        }


class OllamaModel(Equipment):
    """A local model via Ollama.

    Usage:
        model = OllamaModel("llama3")
        response = model.generate("system prompt", [{"role": "user", "content": "hello"}])
    """

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434",
                 temperature: float = 0.7):
        self.name = f"ollama-{model}"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature

    def generate(self, system_prompt: str, messages: list,
                 temperature: float = None) -> str:
        """Generate a response via Ollama."""
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": False,
            "options": {"temperature": temperature or self.temperature},
        }

        req = Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode(),
            method="POST",
        )
        req.add_header("Content-Type", "application/json")
        resp = urlopen(req, timeout=300)
        data = json.loads(resp.read())
        return data.get("message", {}).get("content", "")

    def info(self) -> dict:
        return {"name": self.name, "model": self.model, "base_url": self.base_url}


class LoraAdapter(Equipment):
    """A LoRA adapter for fine-tuned behavior.

    Usage:
        adapter = LoraAdapter("./my-lora-adapter")
        # Attach to LocalModel
        model = LocalModel("meta-llama/Llama-3.1-8B-Instruct")
        model.load()
        adapter.apply(model._model)
    """

    def __init__(self, path: str, alpha: float = 16.0):
        self.name = f"lora-{path.split('/')[-1]}"
        self.path = path
        self.alpha = alpha

    def apply(self, base_model):
        """Apply LoRA adapter to a loaded model."""
        try:
            from peft import PeftModel
        except ImportError:
            raise ImportError("pip install peft to use LoRA adapters")

        # base_model is the transformers model
        self._peft = PeftModel.from_pretrained(base_model, self.path)
        return self._peft

    def info(self) -> dict:
        return {"name": self.name, "path": self.path, "alpha": self.alpha}
