# Impressão de Etiquetas em Massa

Aplicativo com interface gráfica para imprimir etiquetas de equipamentos em lote, enviando comandos ZPL direto para a impressora via rede (TCP, porta 9100).

## Como usar

1. Abra o `Etiquetas.exe`.
2. Confira o **IP** e a **porta** da impressora e clique em **Testar conexão**.
3. Cole os códigos na caixa de texto (**um por linha**) ou clique em **Abrir arquivo .txt**.
4. Clique em **IMPRIMIR** e confirme.

O IP e a porta ficam salvos em `config_etiquetas.json`, na mesma pasta do executável.

## Modelo da etiqueta

Cada código gera uma etiqueta com:

- o código em texto;
- o mesmo código em DataMatrix.

O layout está definido na constante `TEMPLATE_ZPL` em `etiquetas.py`. Para mudar o padrão da etiqueta, edite esse trecho e gere o executável novamente.

## Requisitos

- Windows com acesso de rede à impressora (IP e porta 9100 liberados).
- Impressora compatível com ZPL (ex.: Zebra).

Para quem só usa o `.exe`, não é necessário instalar Python nem nenhuma outra ferramenta.

## Para desenvolvedores

O app usa apenas a biblioteca padrão do Python (tkinter, socket), sem dependências externas.

Rodar direto pelo Python:

```Python
python etiquetas.py
```

Gerar o executável (requer `pip install pyinstaller`):

```Python
python -m PyInstaller --onefile --windowed --name "Etiquetas" etiquetas.py
```

O arquivo final fica em `dist/Etiquetas.exe`.

## Problemas comuns

| Problema                                | O que fazer                                                                                          |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| "Não foi possível conectar"           | Verifique o IP, se a impressora está ligada e se o computador alcança a rede dela (VLAN/VPN).      |
| Windows exibe "protegeu seu computador" | Clique em**Mais informações** e depois em **Executar assim mesmo**.                    |
| IP volta ao padrão a cada abertura     | A pasta do`.exe` é somente leitura; copie o executável para uma pasta com permissão de escrita. |
