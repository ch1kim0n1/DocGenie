# Plugin Development

DocGenie supports parser extensibility through `ParserPlugin` and runtime registration.

## Runtime registration

```python
from pathlib import Path
from docgenie.models import ParseResult
from docgenie.parsers import ParserPlugin, ParserRegistry


class RubyParser(ParserPlugin):
    def __init__(self) -> None:
        super().__init__(name="ruby", languages={"ruby"}, priority=40)

    def parse(self, content: str, path: Path, language: str) -> ParseResult:
        return ParseResult()


registry = ParserRegistry(enable_tree_sitter=True)
registry.register(RubyParser())
```

## Priority and replacement

- Lower `priority` values are chosen first.
- Registering a plugin with the same `name` replaces the existing one.

## Distribution plugins

You can also publish external parsers via entry points in group `docgenie.parsers`.
