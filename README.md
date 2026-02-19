# SekaiTranslator-Parsers (Option A)

This repository is the canonical home of **engine parsers** used by SekaiTranslatorV.

## Goals

- Small, dependency-free core.
- Deterministic **round-trip**: parse → export with unchanged entries must reproduce the exact file bytes
  (except for newline normalization if you choose to enforce it).
- Parsers are pure-Python and do **not** depend on the UI repository.

## Repository layout

```
src/sekai_parsers/
  api.py                 # public types: Entry, ParseResult, Parser
  registry.py            # engine registration + lookup
  engines/
    kirikiri/
      ks_parser.py       # .ks parser (KiriKiri family)
      ks_model.py        # internal helpers for round-trip editing
tests/
  fixtures/
  ...
```

## Adding a new parser

1. Create a folder under `src/sekai_parsers/engines/<engine_id>/`.
2. Implement a parser class that follows `sekai_parsers.api.Parser`.
3. Register it via `sekai_parsers.registry.register_engine(...)`.
4. Add a fixture file and a **round-trip test**.

## Current engines

- `kirikiri.ks` — KiriKiri `.ks` scripts (supports the tag pattern used by *Forbidden Love Wife Sister*).

## License

MIT (see `LICENSE`).
