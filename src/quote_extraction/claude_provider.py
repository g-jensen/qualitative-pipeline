# Completely AI generated - not tested

"""Anthropic Claude provider for LangExtract."""

import concurrent.futures
import dataclasses
from typing import Any, Iterator, Sequence

from langextract.core import base_model
from langextract.core import data
from langextract.core import exceptions
from langextract.core import schema
from langextract.core import types as core_types
from langextract.providers import router

import os

@router.register(
    r"^claude",  # Matches any model_id starting with "claude"
    priority=10,
)
@dataclasses.dataclass(init=False)
class ClaudeLanguageModel(base_model.BaseLanguageModel):
    """Language model inference using Anthropic's Claude API."""

    model_id: str = "claude-haiku-4-5"
    api_key: str | None = None
    format_type: data.FormatType = data.FormatType.JSON
    temperature: float | None = None
    max_workers: int = 10
    _client: Any = dataclasses.field(default=None, repr=False, compare=False)
    _extra_kwargs: dict[str, Any] = dataclasses.field(
        default_factory=dict, repr=False, compare=False
    )

    @property
    def requires_fence_output(self) -> bool:
        """Claude requires fence output for parsing."""
        return True

    def __init__(
        self,
        model_id: str = "claude-haiku-4-5",
        api_key: str | None = None,
        format_type: data.FormatType = data.FormatType.JSON,
        temperature: float | None = None,
        max_workers: int = 10,
        **kwargs,
    ) -> None:
        """Initialize the Claude language model.

        Args:
            model_id: The Claude model ID to use (e.g., 'claude-3-5-sonnet-20241022').
            api_key: API key for Anthropic service.
            format_type: Output format (JSON or YAML).
            temperature: Sampling temperature.
            max_workers: Maximum number of parallel API calls.
            **kwargs: Ignored extra parameters.
        """
        try:
            import anthropic
        except ImportError as e:
            raise exceptions.InferenceConfigError(
                "Claude provider requires anthropic package. "
                "Install with: pip install anthropic"
            ) from e

        self.model_id = model_id
        self.api_key = (api_key or os.getenv("LANGEXTRACT_API_KEY"))
        self.format_type = format_type
        self.temperature = temperature
        self.max_workers = max_workers

        if not self.api_key:
            raise exceptions.InferenceConfigError("API key not provided.")

        self._client = anthropic.Anthropic(api_key=self.api_key)

        super().__init__(
            constraint=schema.Constraint(constraint_type=schema.ConstraintType.NONE)
        )
        self._extra_kwargs = kwargs or {}

    def _process_single_prompt(
        self, prompt: str, config: dict
    ) -> core_types.ScoredOutput:
        """Process a single prompt and return a ScoredOutput."""
        try:
            normalized_config = config.copy()

            system_message = ""
            if self.format_type == data.FormatType.JSON:
                system_message = (
                    "You are a helpful assistant that responds in JSON format. "
                    "Wrap your JSON response in ```json and ``` code fences."
                )
            elif self.format_type == data.FormatType.YAML:
                system_message = (
                    "You are a helpful assistant that responds in YAML format. "
                    "Wrap your YAML response in ```yaml and ``` code fences."
                )

            api_params = {
                "model": self.model_id,
                "max_tokens": normalized_config.get("max_output_tokens", 4096),
                "messages": [{"role": "user", "content": prompt}],
            }

            if system_message:
                api_params["system"] = system_message

            temp = normalized_config.get("temperature", self.temperature)
            if temp is not None:
                api_params["temperature"] = temp

            if (v := normalized_config.get("top_p")) is not None:
                api_params["top_p"] = v

            for key in ["top_k", "stop_sequences"]:
                if (v := normalized_config.get(key)) is not None:
                    api_params[key] = v

            response = self._client.messages.create(**api_params)

            output_text = response.content[0].text

            return core_types.ScoredOutput(score=1.0, output=output_text)

        except Exception as e:
            raise exceptions.InferenceRuntimeError(
                f"Claude API error: {str(e)}", original=e
            ) from e

    def infer(
        self, batch_prompts: Sequence[str], **kwargs
    ) -> Iterator[Sequence[core_types.ScoredOutput]]:
        """Runs inference on a list of prompts via Claude's API.

        Args:
            batch_prompts: A list of string prompts.
            **kwargs: Additional generation params (temperature, top_p, etc.)

        Yields:
            Lists of ScoredOutputs.
        """
        merged_kwargs = self.merge_kwargs(kwargs)

        config = {}

        temp = merged_kwargs.get("temperature", self.temperature)
        if temp is not None:
            config["temperature"] = temp
        if "max_output_tokens" in merged_kwargs:
            config["max_output_tokens"] = merged_kwargs["max_output_tokens"]
        if "top_p" in merged_kwargs:
            config["top_p"] = merged_kwargs["top_p"]

        for key in ["top_k", "stop_sequences"]:
            if key in merged_kwargs:
                config[key] = merged_kwargs[key]

        # Use parallel processing for batches larger than 1
        if len(batch_prompts) > 1 and self.max_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=min(self.max_workers, len(batch_prompts))
            ) as executor:
                future_to_index = {
                    executor.submit(
                        self._process_single_prompt, prompt, config.copy()
                    ): i
                    for i, prompt in enumerate(batch_prompts)
                }

                results: list[core_types.ScoredOutput | None] = [None] * len(
                    batch_prompts
                )
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        results[index] = future.result()
                    except Exception as e:
                        raise exceptions.InferenceRuntimeError(
                            f"Parallel inference error: {str(e)}", original=e
                        ) from e

                for result in results:
                    if result is None:
                        raise exceptions.InferenceRuntimeError(
                            "Failed to process one or more prompts"
                        )
                    yield [result]
        else:
            # Sequential processing for single prompt or worker
            for prompt in batch_prompts:
                result = self._process_single_prompt(prompt, config.copy())
                yield [result]
