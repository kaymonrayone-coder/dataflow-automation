# Como contribuir

1. Abra uma issue com o problema ou proposta e um exemplo mínimo com dados fictícios.
2. Faça um fork e crie uma branch para a alteração.
3. Instale com `python -m pip install -e '.[dev]'`.
4. Acrescente testes que comprovem o comportamento e execute `python -m pytest -q`.
5. Execute `python -m build` e atualize a documentação quando necessário.
6. Abra um pull request explicando problema, solução, testes e limitações.

Prefira mudanças pequenas, funções com responsabilidade clara e compatibilidade com Python 3.10+.
Nunca inclua segredos, dados pessoais ou materiais proprietários. Relate suspeitas de segurança
sem publicar credenciais ou exemplos exploráveis com dados reais.
