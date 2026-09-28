# 🤝 Diretrizes de Contribuição (Contributing Guide)

Agradecemos o interesse em contribuir com o **Cartela**! Este projeto segue padrões rígidos de rigor matemático, tipagem e testes automatizados.

---

## 1. Padrão de Desenvolvimento TDD (Test-Driven Development)

Todas as novas funcionalidades combinatórias ou estatísticas devem ser desenvolvidas com ciclo TDD estrito:
1. **RED:** Crie primeiro o caso de teste em `tests/test_engine.py` demonstrando a propriedade matemática esperada.
2. **GREEN:** Implemente a menor alteração suficiente no motor para fazer o teste passar.
3. **REFACTOR:** Otimize a complexidade assintótica e legibilidade mantendo 100% dos testes verdes.

---

## 2. Executando a Suíte de Testes Localmente

```bash
python -m unittest discover -v tests
```

Todos os 12 testes devem passar antes de abrir qualquer Pull Request.

---

## 3. Padrão de Commits Semânticos

Seguimos a convenção de [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` Novas funcionalidades combinatórias ou modelos estatísticos.
- `fix:` Correções de bugs ou falhas de cálculo.
- `docs:` Alterações em documentação ou especificações matemáticas.
- `refactor:` Melhorias de arquitetura ou otimização sem alterar comportamento externo.
- `test:` Adição ou expansão de testes unitários.
