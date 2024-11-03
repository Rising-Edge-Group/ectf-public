# ectf-public

```
Usage: cli.py [OPTIONS] COMMAND [ARGS]...

  Command Line Interface (CLI) for interacting with echoCTF.RED

  Default configuration file: ~/.echoctf.json

Options:
  --config TEXT  Path to the JSON configuration file.
  --help         Show this message and exit.

Commands:
  claim  Attempts to claim the specified `FLAG`.
  spin   Spins the target specified by `TARGET_ID`.
```

Configuration file sample structure:
```json
{
    "instance_url" : "https://echoctf.red/",
    "_identity-red": "REDACTED"
}

```
