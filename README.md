# SekaiTranslator-Parsers

Esse é o repositório oficial de **parsers** do SekaiTranslatorV

## Layout

```
src/sekai_parsers/
  api.py                 # pública tipos: Entry, ParseResult, Parser
  registry.py            # engine registro + busca
  engines/
    kirikiri/
      ks_parser.py       # .ks parser (KiriKiri family)
      ks_model.py        # helpers internos para edição dos arquivos Scripts
tests/
  fixtures/
  ...
```

## Adicionando um novo parser

1. Crie uma pasta em`src/sekai_parsers/engines/<engine_id>/`.
2. Implemente uma classe com base no`sekai_parsers.api.Parser`.
3. Regisstre `sekai_parsers.registry.register_engine(...)`.
4. Adicione im arquivo de fixture file im **arquivo de teste**.

## Engines suportadas

- `kirikiri.ks` — KiriKiri `.ks` scripts

## Licença

MIT (ver `LICENSE`).




