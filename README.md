# SekaiTranslator-Parsers

Esse é o repositório oficial de **parsers** do SekaiTranslatorV

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

- `kirikiri.ks` — KiriKiri `.ks` scripts

## License

MIT (see `LICENSE`).



