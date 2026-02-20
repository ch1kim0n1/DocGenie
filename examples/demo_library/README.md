# demo_library

A python application with comprehensive functionality and modern architecture.



## Features


- 🔄 Asynchronous processing

- 🏗️ Object-oriented architecture





## Requirements


- See installation instructions below


## Installation


### Install Python dependencies

```bash
pip install -r requirements.txt
```




## Usage


### Run the application

```python
python main.py
```





## Project Structure

```
├── .docgenie.yaml
├── cli.py
├── docs.html
├── README.md
└── requirements.txt
├── .docgenie/
│   └── cache.json
├── mathlib/
│   ├── arithmetic.py
│   ├── async_utils.py
│   ├── geometry.py
│   └── __init__.py
├── textlib/
│   ├── formatter.py
│   └── __init__.py
```


## Architecture

This python application is built with python and consists of:

- **38** functions across the codebase
- **6** classes/components
- **12** source files analyzed
- **6** programming languages used

### Language Distribution


- **Python**: 7 files

- **Yaml**: 1 files

- **Text**: 1 files

- **Html**: 1 files

- **Markdown**: 1 files

- **Json**: 1 files



## API Reference

### Functions


#### `main()`


Entry point for the demo_library CLI.

Prints a brief demo of each module's capabilities and exits.

Returns:
    0 on success.



#### `add(a, b)`


Add two numbers together and return their sum.

Args:
    a: The first operand.
    b: The second operand.

Returns:
    The sum of a and b.



#### `subtract(a, b)`


Subtract b from a and return the result.

Args:
    a: The minuend.
    b: The subtrahend.

Returns:
    The difference a - b.



#### `multiply(a, b)`


Multiply two numbers and return their product.

Args:
    a: The first factor.
    b: The second factor.

Returns:
    The product of a and b.



#### `divide(a, b)`


Divide a by b and return the quotient.

Args:
    a: The dividend.
    b: The divisor.

Returns:
    The quotient a / b.

Raises:
    ZeroDivisionError: If b is zero.



#### `power(base, exponent)`


Raise base to an integer exponent.

Args:
    base: The base value.
    exponent: The integer exponent (may be negative).

Returns:
    base raised to the power of exponent.



#### `clamp(value, minimum, maximum)`


Clamp value to the inclusive range [minimum, maximum].

Args:
    value: The value to clamp.
    minimum: The lower bound.
    maximum: The upper bound.

Returns:
    value if within range, else the nearest bound.



#### `async_compute(value, delay)`


Simulate an async computation with an optional delay.

Args:
    value: The integer to double.
    delay: Seconds to sleep before returning (default 0).

Returns:
    value multiplied by 2.



#### `batch_compute(values)`


Compute values concurrently using asyncio.gather.

Args:
    values: A list of integers to process.

Returns:
    A list of results, each element doubled.



#### `retry(coro_fn, retries, delay)`


Retry an async coroutine function up to ``retries`` times.

Args:
    coro_fn: A zero-argument async callable.
    retries: Maximum number of attempts.
    delay: Seconds between attempts.

Returns:
    The result of the first successful invocation.

Raises:
    Exception: The last exception if all attempts fail.






### Classes


#### `Shape`


Abstract base class for geometric shapes.

All concrete shapes should implement :meth:`area` and :meth:`perimeter`.



**Methods:**

- `area(self)`

- `perimeter(self)`

- `describe(self)`




#### `Circle`


A circle defined by its radius.

Args:
    radius: The radius of the circle (must be positive).



**Methods:**

- `__init__(self, radius)`

- `area(self)`

- `perimeter(self)`

- `from_diameter(cls, diameter)`




#### `Rectangle`


A rectangle defined by width and height.

Args:
    width: The horizontal dimension.
    height: The vertical dimension.



**Methods:**

- `__init__(self, width, height)`

- `area(self)`

- `perimeter(self)`

- `is_square(self)`

- `square(cls, side)`




#### `Triangle`


A triangle defined by three side lengths.

Uses Heron's formula for area computation.

Args:
    a: Length of the first side.
    b: Length of the second side.
    c: Length of the third side.



**Methods:**

- `__init__(self, a, b, c)`

- `area(self)`

- `perimeter(self)`




#### `TextFormatter`


Formats text with configurable prefix, suffix, and transformation rules.

Args:
    prefix: String prepended to all formatted text.
    suffix: String appended to all formatted text.



**Methods:**

- `__init__(self, prefix, suffix)`

- `format(self, text)`

- `format_upper(self, text)`

- `word_count(text)`

- `bold(cls)`




#### `MarkdownFormatter`


Extended formatter with Markdown-specific helpers.

Inherits from :class:`TextFormatter` and adds heading and link generation.



**Methods:**

- `heading(self, text, level)`

- `link(self, label, url)`












## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request



## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact


- Repository: [ch1kim0n1/DocGenie](https://github.com/ch1kim0n1/DocGenie.git)


- Latest commit: Fix path assertions in tests for Windows compatibility

Update test_exceptions.py to use `str(path)` instead of hardcoded POSIX paths in assertions.
This resolves failures on Windows where paths use backslashes.


---

*This README was automatically generated by [DocGenie](https://github.com/docgenie/docgenie) on 2026-02-20 02:12:07*