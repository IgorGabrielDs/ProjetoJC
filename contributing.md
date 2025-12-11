# 🧩 Guia de Contribuição — Projeto JC

Obrigado por querer contribuir com o **Projeto JC — Portal de Notícias Interativo**!  
Este documento explica **como montar o ambiente**, **rodar o projeto** e **enviar contribuições** (issues e pull requests) de forma organizada.

> ⚠️ Este arquivo é o `CONTRIBUTING.md`.  
> Toda descrição “de vitrine” do sistema (o que é o projeto, objetivos, prints, métricas etc.) deve ficar no `README.md`, não aqui.

---

## 1. Formas de contribuir

Você pode ajudar o Projeto JC de várias maneiras:

- 🐛 **Correção de bugs** (backend, frontend ou jogos).
- ✨ **Novas funcionalidades** baseadas nas histórias de usuário (notícias, Top 3, Ler Mais Tarde, recomendações, enquetes, etc.).
- 🎨 **Melhorias de UI/UX** (HTML/CSS/JS, responsividade, acessibilidade).
- 🧪 **Testes automatizados** (`pytest`, `pytest-django`).
- 📚 **Documentação** (melhorar este `CONTRIBUTING`, docstrings, comentários, guias internos).

Antes de começar algo maior:

1. Verifique se já existe uma **Issue** para o que você quer fazer.  
2. Se não existir, crie uma **nova Issue** explicando a ideia/bug e marque o escopo.  
3. Comente na Issue dizendo que você pretende trabalhar nela.

---

## 2. Pré-requisitos

Para rodar o Projeto JC localmente, você precisa de:

- [Python 3.13+](https://www.python.org/)  
- [Git](https://git-scm.com/)  
- `pip` (já vem com o Python)  
- Opcional, mas recomendado: **ambiente virtual** (`venv`)

Banco de dados em desenvolvimento: **SQLite** (nenhuma instalação extra necessária).

---

## 3. Clonando o repositório

Se você tem acesso direto ao repositório principal:

```bash
git clone https://github.com/IgorGabrielDs/ProjetoJC.git
cd ProjetoJC
```

Se você **não** faz parte da organização / time principal, use o fluxo de **fork** (ver seção 8).

---

## 4. Criando e ativando o ambiente virtual

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```bash
python -m venv .venv
.\.venv\Scriptsctivate
```

Você saberá que o ambiente está ativo quando aparecer algo como `(.venv)` no início da linha do terminal.

---

## 5. Instalando dependências

Com o ambiente virtual **ativo**:

```bash
pip install -r requirements.txt
```

Se ocorrer algum erro:

- Verifique se o Python usado é o mesmo do ambiente virtual (`python --version`).
- Verifique se o `pip` é o do ambiente virtual (`which pip` ou `where pip` no Windows).

---

## 6. Configurando variáveis de ambiente

O Projeto JC usa variáveis de ambiente para chaves sensíveis (por exemplo: `SECRET_KEY`, chaves de APIs etc.).

O caminho mais simples em desenvolvimento é criar um arquivo `.env` na raiz do projeto (mesmo nível de `manage.py`) com, pelo menos:

```env
# NÃO usar esta chave em produção
SECRET_KEY=django-insecure-dev-key

# Ativar modo debug em desenvolvimento
DEBUG=True

# Opcional: chaves para recursos de IA / APIs externas
# OPENAI_API_KEY=sua_chave_aqui
# GEMINI_API_KEY=sua_chave_aqui
```

> Em produção, essas variáveis devem ser configuradas no ambiente (Azure, GitHub Actions, etc.), **nunca commitadas**.

---

## 7. Rodando o projeto localmente

### 7.1 Aplicar migrações

Na raiz do projeto (onde está `manage.py`):

```bash
python manage.py migrate
```

### 7.2 Criar um superusuário

```bash
python manage.py createsuperuser
```

Siga as instruções (nome de usuário, e-mail, senha).

### 7.3 Iniciar o servidor de desenvolvimento

```bash
python manage.py runserver
```

Acesse no navegador:

- Portal: http://127.0.0.1:8000/  
- Admin: http://127.0.0.1:8000/admin/

Se algo der erro:

- Verifique se o ambiente virtual está ativo.
- Veja se existe alguma mensagem ligada a `ALLOWED_HOSTS`, migrações pendentes ou dependências faltando.
- Em desenvolvimento, **mantenha `DEBUG=True`** até tudo funcionar.

---

## 8. Fluxo de Git e Pull Requests

### 8.1 Fork (para contribuidores externos)

Se você não tem permissão de escrita no repositório principal:

1. Clique em **“Fork”** na página do GitHub.  
2. Clone o **seu** fork:

   ```bash
   git clone https://github.com/<seu-usuario>/ProjetoJC.git
   cd ProjetoJC
   ```

3. (Opcional) Adicione o repositório original como `upstream`:

   ```bash
   git remote add upstream https://github.com/IgorGabrielDs/ProjetoJC.git
   ```

### 8.2 Criando uma branch por tarefa

Sempre trabalhe em uma branch separada da `main`:

```bash
git checkout -b feature/minha-nova-feature
# ou
git checkout -b fix/ajuste-top3-mobile
```

Evite trabalhar direto na `main`.

### 8.3 Mantendo sua branch atualizada

Antes de abrir um PR, sincronize com a `main` mais recente:

```bash
git checkout main
git pull origin main

git checkout feature/minha-nova-feature
git merge main
# Resolva conflitos, se houver
```

Se estiver usando fork:

```bash
git fetch upstream
git checkout main
git merge upstream/main

git checkout feature/minha-nova-feature
git merge main
```

### 8.4 Commits

Use mensagens de commit curtas e descritivas:

- `feat: adicionar submenu rápido na home`
- `fix: corrigir ordenação do Top 3 da semana`
- `test: adicionar testes de Ler Mais Tarde`
- `style: ajustar CSS do Sudoku no mobile`

### 8.5 Abrindo o Pull Request

1. Envie sua branch para o GitHub:

   ```bash
   git push origin feature/minha-nova-feature
   ```

2. No GitHub, abra um **Pull Request** (PR) apontando para a `main` do repositório original.
3. Na descrição do PR, inclua:
   - Resumo do que foi feito.
   - Qual **Issue** ou **história de usuário** está sendo atendida (ex.: “resolve #7”).
   - Prints de tela, se houver mudanças visuais.
   - Passos para testar a funcionalidade.

---

## 9. Rodando testes

O Projeto JC usa **pytest** e **pytest-django**.

Para rodar **todos os testes**:

```bash
pytest
# ou
pytest -q
```

Antes de enviar um PR:

- ✅ Rode os testes localmente.  
- ✅ Verifique se as funcionalidades principais continuam funcionando:
  - Home e navegação por notícias.
  - Top 3 da semana.
  - Ler Mais Tarde.
  - Caça-links (jogo e histórico).
  - Sudoku JC (jogo e retomada).
  - Enquetes nas notícias (quando existirem).

Se adicionar uma nova funcionalidade ou corrigir um bug:

- Sempre que possível, **inclua ou atualize testes** para cobrir o comportamento.

---

## 10. Padrões de código

### 10.1 Python / Django

- Siga o **PEP 8** quando possível.
- Prefira nomes descritivos para funções, variáveis e classes.
- Evite funções muito grandes; quebre em funções menores quando fizer sentido.
- Em Django:
  - Views organizadas por app (`noticias`, `caca_links`, `sudoku`, etc.).
  - Use templates por app: `app/templates/app/arquivo.html`.
  - Use estáticos por app: `app/static/app/css/...`, `app/static/app/js/...`.

### 10.2 HTML / CSS / JS

- Layout **mobile-first** e responsivo.
- Reutilize classes e componentes já existentes sempre que possível.
- Evite criar CSS duplicado para o mesmo padrão visual.
- Mantenha o HTML o mais semântico possível (`<main>`, `<section>`, `<article>`, etc.).
- Teste no mínimo:
  - Versão mobile.
  - Versão desktop.

### 10.3 Idioma e textos

- Interfaces e mensagens para o usuário: **português do Brasil**.
- Comentários de código: podem ser em PT-BR ou EN, mas mantenha consistência dentro do arquivo.

---

## 11. Issues: como abrir e o que informar

Ao criar uma **Issue**, tente incluir:

- **Tipo**: `bug`, `feature`, `improvement`, `docs`, `question`.
- **Resumo** em uma frase no título.
- **Descrição detalhada**:
  - Passos para reproduzir (se for bug).
  - Comportamento atual vs esperado.
  - Navegador/ambiente (se for problema de front).
  - Prints ou GIFs rápidos (opcional, mas ajuda muito).

Exemplos de bons títulos:

- `Bug: botão "Ler mais tarde" não atualiza estado no mobile`
- `Feature: adicionar ranking de Sudoku por tempo de resolução`
- `Improvement: melhorar contraste dos links do Caça-links`

---

## 12. Histórias de usuário e BDD

O Projeto JC é guiado por **histórias de usuário em formato BDD** (ex.: “Compartilhar notícias”, “Filtrar notícias”, “Top 3 da semana”, “Caça-links”, “Sudoku JC”, “Enquete na notícia” etc.).

Ao propor uma mudança:

- Verifique se já existe uma **história** relacionada.
- Certifique-se de que o comportamento continua **coerente com os cenários BDD** (Dado/Quando/Então).
- Se estiver criando algo novo, tente escrever pelo menos um rascunho de cenário BDD na Issue ou no PR.

---

## 13. Dúvidas e suporte

Se você tiver dúvidas:

- Abra uma **Issue** com o tipo `question` explicando exatamente onde travou (setup, testes, código, etc.).
- Se a dúvida for sobre uma Issue existente, pergunte diretamente nos comentários dela.

---

Obrigado por contribuir com o Projeto JC 💙  
Sua ajuda faz diferença para evoluir o portal, melhorar a experiência dos leitores e fortalecer a fidelização no ambiente digital.
