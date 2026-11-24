# Abrir e publicar pelo Visual Studio Code

## 1. Abrir o código

1. Extraia o ZIP inteiro. Não abra o projeto de dentro do arquivo compactado.
2. No Visual Studio Code, use **Arquivo > Abrir Pasta** e escolha a pasta `Santo_Bigode`, onde estão `server.py`, `README.md` e `web/`.
3. Você também pode abrir `Santo_Bigode.code-workspace` pelo VS Code.

O código já está organizado como raiz de um repositório. A pasta `.vscode` contém configurações de execução, depuração e testes. A pasta `docs/` contém imagens e detalhes para apresentação no GitHub.

## 2. Executar no computador

É necessário ter Python 3.10 ou superior instalado. No Windows, marque a opção de adicionar Python ao PATH durante a instalação.

No terminal integrado do VS Code (**Terminal > Novo Terminal**), execute:

```powershell
py -3 server.py
```

Se o comando `py` não existir, tente:

```powershell
python server.py
```

No macOS/Linux:

```bash
python3 server.py
```

O programa abre no navegador em `http://127.0.0.1:8765`. Não precisa de `pip install` nem de Java. Não use Live Server para iniciar esta aplicação: o backend Python precisa estar em execução.

No primeiro uso, o terminal exibe o link temporário para você criar o administrador. Defina sua própria senha. O banco será criado em `data/`, que está excluída do Git. Para encerrar, pressione Ctrl+C no terminal.

### Executar com F5

Instale as extensões recomendadas **Python** e **Python Debugger**, da Microsoft. Use `Ctrl+Shift+P > Python: Select Interpreter` para selecionar o Python instalado. Depois pressione **F5** e escolha **Santo Bigode: iniciar aplicação**. O arquivo `.vscode/launch.json` já está configurado.

Também há tarefas em **Terminal > Executar Tarefa** para iniciar a aplicação e executar os testes Python. Não inicie duas instâncias ao mesmo tempo na mesma porta.

## 3. Subir para o GitHub pelo VS Code

Tenha o Git instalado no computador: https://git-scm.com/downloads

1. Abra **Controle do Código-Fonte / Source Control** com `Ctrl+Shift+G`.
2. Clique em **Inicializar Repositório / Initialize Repository**.
3. Prepare os arquivos para commit pelo botão **+** ao lado de Alterações / Changes.
4. Escreva uma mensagem, por exemplo: `Adiciona Santo Bigode com gestão e visagismo`.
5. Clique em **Commit**. Se solicitado, configure seu nome e e-mail do Git.
6. Abra `Ctrl+Shift+P` e execute **Publish to GitHub / Publicar no GitHub**.
7. Entre na sua conta, escolha o nome do repositório e sua visibilidade.

O VS Code cria o repositório remoto e envia os commits. O arquivo `README.md` já apresenta o projeto e referencia os prints em `docs/`.

### Se o Git solicitar seu nome e e-mail

No terminal do projeto, configure os dados que deseja associar aos commits. O e-mail pode ser o endereço privado `noreply` fornecido pelo GitHub. Substitua os exemplos abaixo pelos seus dados:

```bash
git config user.name "Seu Nome"
git config user.email "seu-email-de-commit@example.com"
```

Esses comandos configuram apenas este projeto. Depois tente o commit novamente.

## 4. O que acompanha esta entrega

- Aplicação local executável: Python, JavaScript, HTML, CSS e SQLite.
- Modelos e runtimes usados na análise local de foto, com as licenças correspondentes.
- Configuração do VS Code para depuração e testes.
- Núcleo TypeScript da API online, esquema e migrações para estudo; a infraestrutura completa da hospedagem não está empacotada para implantação automática em outro provedor.
- README, créditos, prints e documentação da proposta.
- `.gitignore` para não versionar banco, backups, arquivos de ambiente e dependências locais.

As fotografias externas dos prints foram substituídas por placeholders SVG na aplicação desta pasta. Use fotos próprias ou autorizadas para personalizar o portfólio. O pacote não inclui credenciais, bancos reais, a agenda antiga ou uma pasta `.git` pré-configurada.

Subir o código para o GitHub não publica o servidor Python nem sincroniza o banco local com a versão online. Consulte o README para a arquitetura e os limites do protótipo.

## Referências oficiais

- Git no VS Code: https://code.visualstudio.com/docs/sourcecontrol/quickstart
- Depuração Python: https://code.visualstudio.com/docs/python/debugging
