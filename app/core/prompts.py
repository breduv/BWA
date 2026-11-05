import re
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PROMPTS_FILE = Path(__file__).resolve().parents[2] / "config" / "prompts.yml"
COMMAND_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
BUILTIN_COMMANDS = {
    "start": "Начать работу с ботом",
    "help": "Посмотреть справку и список режимов",
}


def build_system_prompt(mode_prompt: str, tool_policy: str) -> str:
    return f"{mode_prompt}\n\n{tool_policy}"


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently overriding a command."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict:
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise TypeError(f"YAML mapping key must be text, got {key!r}")
            if key in keys:
                raise ValueError(f"Duplicate YAML key: {key!r}")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class PromptMode:
    name: str
    description: str
    prompt: str


@dataclass(frozen=True)
class PromptConfig:
    search_prompt: str
    tool_policy: str
    modes: dict[str, PromptMode]


def load_prompts(path: Path = DEFAULT_PROMPTS_FILE) -> PromptConfig:
    """Read and validate shared prompts and modes on application startup.

    Raises a clear exception if the file is missing or a mode is malformed.
    """
    try:
        with path.open(encoding="utf-8") as file:
            config = yaml.load(file, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(config, dict) or not isinstance(config.get("modes"), dict):
        raise TypeError(f"{path}: expected a 'modes' mapping")
    if set(config) != {"search_prompt", "tool_policy", "modes"}:
        raise ValueError(
            f"{path}: expected only 'search_prompt', 'tool_policy', and 'modes' root keys"
        )
    for key in ("search_prompt", "tool_policy"):
        if not isinstance(config[key], str) or not config[key].strip():
            raise ValueError(f"{path}: {key} must be non-empty text")

    entries = config["modes"]
    max_modes = 100 - len(BUILTIN_COMMANDS)
    if not 1 <= len(entries) <= max_modes:
        raise ValueError(f"{path}: expected 1 to {max_modes} prompt modes")

    modes: dict[str, PromptMode] = {}
    for name, value in entries.items():
        if not isinstance(name, str) or not COMMAND_PATTERN.fullmatch(name):
            raise ValueError(f"{path}: invalid Telegram command {name!r}")
        if name in BUILTIN_COMMANDS:
            raise ValueError(f"{path}: /{name} is reserved for a built-in command")
        if not isinstance(value, dict) or set(value) != {"description", "prompt"}:
            raise ValueError(
                f"{path}: /{name} must contain only 'description' and 'prompt'"
            )

        description, prompt = value["description"], value["prompt"]
        if not isinstance(description, str) or not 3 <= len(description.strip()) <= 256:
            raise ValueError(f"{path}: /{name} description must be 3–256 characters")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"{path}: /{name} prompt must be non-empty text")

        modes[name] = PromptMode(name, description.strip(), prompt.strip())

    return PromptConfig(
        search_prompt=config["search_prompt"].strip(),
        tool_policy=config["tool_policy"].strip(),
        modes=modes,
    )
