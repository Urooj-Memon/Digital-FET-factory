"""Minimal stub for the `agents` package used in tests.

The real project would depend on a sophisticated library that provides Agent
creation, a Runner, and model settings. For the purpose of the unit tests we only
need a tiny subset of functionality:

* `Agent` class exposing `name`, `instructions`, `tools`, `model`, and
  `model_settings` attributes.
* `Runner` with a static async `run` method that returns an object with a
  `final_output` attribute – the tests never call it, but other modules import
  it.
* `ModelSettings` simple data holder.
* `function_tool` decorator that wraps async tool functions so they expose an
  `on_invoke_tool` method matching the test expectations. The wrapper parses the
  JSON‑encoded input, constructs the Pydantic model defined in the function's
  signature, invokes the original async function, and returns the JSON string of
  the result. If the wrapped function already returns a JSON string, it is passed
  through unchanged.

This stub is deliberately lightweight and avoids external dependencies.
"""

import json
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Awaitable, List


@dataclass
class ModelSettings:
    """Container for model configuration settings used by the real SDK."""
    temperature: float = 0.0
    top_p: float = 1.0


class Agent:
    """Simple representation of an agent.

    The real SDK would provide many more features, but the tests only verify that
    the object stores the provided name, instructions and tools list.
    """

    def __init__(self, *, name: str, instructions: str, tools: List[Any], model: str, model_settings: ModelSettings):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.model = model
        self.model_settings = model_settings


class Runner:
    """Placeholder for the asynchronous runner used to execute an agent.

    It returns an object with a `final_output` attribute so that code expecting a
    result can access it without raising errors.
    """

    @staticmethod
    async def run(agent: Agent, input_messages: List[dict]) -> Any:
        class Result:
            def __init__(self, output: str):
                self.final_output = output
        # For testing we simply return a generic placeholder string.
        return Result(output="<agent result placeholder>")


def function_tool(func: Callable[[Any], Awaitable[Any]]) -> Callable[[Any], Awaitable[Any]]:
    """Decorator that equips an async tool function with `on_invoke_tool`.

    The FastAPI‑style tests call `tool.on_invoke_tool(context, json_string)`. The
    implementation parses the JSON, builds the Pydantic model defined in the first
    parameter of the original function, calls the function, and returns the JSON
    encoding of the result. If the wrapped function already returns a JSON string,
    it is passed through unchanged.
    """

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    async def on_invoke_tool(self, _context, json_input: str) -> str:
        # Load the JSON payload.
        payload = json.loads(json_input)
        # Determine the expected Pydantic model from the function signature.
        sig = inspect.signature(func)
        param = next(iter(sig.parameters.values()))
        model_cls = param.annotation
        # Instantiate the model.
        model_instance = model_cls(**payload)
        # Call the original async function.
        result = await func(model_instance)
        # If the result is already a JSON string, return it directly.
        if isinstance(result, str):
            return result
        return json.dumps(result)

    # Attach the method to the wrapper instance.
    wrapper.on_invoke_tool = on_invoke_tool.__get__(wrapper)
    return wrapper
