# SekaiTranslator — Parsers

> Repositório oficial de **parsers** do SekaiTranslatorV.  
> Cada engine representa um motor de visual novel suportado, com seus respectivos perfis por jogo.

---

## 🌿 Branches

| Branch | Finalidade |
|---|---|
| `main` | Apenas releases estáveis |
| `Features/engine` | Novas engines e parsers em desenvolvimento |

> ⚠️ Toda engine nova deve ser adicionada via `Features/engine` antes de ir para o `main`.

---

## 📁 Estrutura do projeto

```
src/sekai_parsers/
├── api.py                  # Tipos públicos: Entry, ParseResult, Parser
├── engine_registry.py      # Registro e lookup de engines
└── engines/
    ├── kirikiri/
    │   ├── ks_parser.py    # Parser .ks (família KiriKiri)
    │   ├── ks_model.py     # Helpers internos
    │   └── profiles/
    │       └── yandere.py  # Perfil Yandere
    ├── musica/
    │   ├── sc_parser.py    # Parser .sc (engine Musica)
    │   └── profiles/
    │       ├── ef.py       # Perfil ef
    │       └── eden.py     # Perfil eden
    ├── artemis/
    │   ├── ast_parser.py   # Parser .ast (engine Artemis)
    │   └── profiles/
    │       └── nukitashi.py  # Perfil Nukitashi
    └── yuris/
        └── json_parser.py  # Parser JSON (engine Yuris)

tests/
└── fixtures/
```

---

## ⚙️ Engines suportadas

| Engine ID | Extensão | Jogo / Engine |
|---|---|---|
| `kirikiri.ks` | `.ks` | KiriKiri / KAG |
| `kirikiri.ks.yandere` | `.ks` | KiriKiri — perfil Yandere |
| `musica.sc` | `.sc` | Engine Musica |
| `musica.sc.ef` | `.sc` | Musica — perfil ef |
| `musica.sc.eden` | `.sc` | Musica — perfil eden |
| `artemis.ast` | `.ast` | Engine Artemis |
| `artemis.ast.nukitashi` | `.ast` | Artemis — perfil Nukitashi |
| `yuris` | `.json` | Engine Yuris |

---

## ➕ Como adicionar um novo parser

1. Crie uma pasta em `src/sekai_parsers/engines/<engine_id>/`
2. Implemente uma classe seguindo a interface `sekai_parsers.api.Parser`
3. Registre com `sekai_parsers.engine_registry.register_engine(...)`
4. Adicione um arquivo de fixture e um **arquivo de testes**
5. Abra seu PR apontando para a branch `Features/engine`

---

## 📄 Licença

MIT — veja o arquivo `LICENSE`.