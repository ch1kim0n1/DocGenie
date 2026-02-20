# Generators API Reference

## ReadmeGenerator

::: docgenie.generator.ReadmeGenerator
    options:
      show_source: true
      heading_level: 3

## HTMLGenerator

::: docgenie.html_generator.HTMLGenerator
    options:
      show_source: true
      heading_level: 3

## Usage

```python
from docgenie import HTMLGenerator, ReadmeGenerator

readme = ReadmeGenerator().generate(analysis_data)
html = HTMLGenerator().generate_from_analysis(analysis_data)
```
