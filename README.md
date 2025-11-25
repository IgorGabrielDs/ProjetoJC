# 📰 Projeto JC — Portal de Notícias Interativo  
### 🌐 [Acesse aqui](https://jcproject.azurewebsites.net/)

## 📌 Descrição  
O **Projeto JC** é o portal de notícias desenvolvido pela **Equipe Plumo (CESAR School)** para o **Jornal do Commercio (JC)**.  
O sistema busca enfrentar a queda nas buscas orgânicas gerada pelo avanço da **IA generativa**, criando uma **experiência personalizada, gamificada e interativa** que incentiva o retorno e a fidelização dos leitores.  

A plataforma combina **conteúdo jornalístico** com **elementos de jogos, recomendações e personalização de leitura**, consolidando o JC como uma marca confiável e inovadora no ambiente digital.

---

## 🎯 Objetivos
- **Fidelizar leitores** através de personalização e interatividade.  
- **Aumentar o tempo médio de leitura e número de páginas por sessão.**  
- **Estimular o segundo clique** com recursos de engajamento.  
- **Oferecer experiência fluida e responsiva** em dispositivos móveis.  

---

## 🚀 Funcionalidades Atuais

### 📰 Portal e Engajamento
- 🔗 **Compartilhar notícias** (WhatsApp, X/Twitter, Facebook).  
- 👍 **Votar em notícias** (sistema de avaliação positiva/negativa).  
- 🏆 **Top 3 da Semana** — destaques mais lidos e votados.  
- 📚 **Ler Mais Tarde** — salvar matérias para leitura posterior.  
- 🧭 **Filtros de assunto** — navegação por temas.  
- 🧠 **Resumo Automático** — integração com IA para condensar textos.

### 🎮 Jogos e Fidelização
- 🎯 **Caça-links** — mini-game interativo que estimula cliques e descoberta de conteúdo.  
- 🔢 **Sudoku JC** — jogo de lógica com salvamento de progresso do usuário.

### 🧩 Autenticação e Gamificação
- 🔐 Login, logout e controle de acesso com `django.contrib.auth`.  

---

## 🧪 Testes e Qualidade
O projeto utiliza **pytest-django** para garantir estabilidade:
- Testes de integração e unidade para views, templates e jogos (`noticias/tests`, `caca_links/tests`, `sudoku/tests`).  
- Ambiente separado de testes (`settings_test.py`).  

Comando para rodar todos os testes:  
```bash
pytest -q
```

---

## ⚙️ Stack Tecnológica
| Camada | Tecnologia |
|--------|-------------|
| **Backend** | Django 5.2 (Python 3.13) |
| **Frontend** | HTML5 • CSS3 • JavaScript |
| **Banco de Dados (Dev/Test)** | SQLite |
| **Hospedagem (Prod)** | Azure App Service + PostgreSQL Flexible Server |
| **Serviços** | WhiteNoise (static files), OpenAI API, Google Trends |
| **CI/CD** | GitHub Actions |
| **Design** | Figma • UI estilo JC |

---

## 📈 Métricas de Sucesso
- ⏱️ Tempo médio de permanência no site  
- 🔁 Taxa de retorno e frequência de leitura  
- 📊 Páginas por sessão  
- 📰 Interação com filtros e jogos  
- 💬 Engajamento em “segundo clique”  

---

Acesse o nosso vídeo de testes automatizados [aqui](https://youtu.be/jgPmHwQA0cM)

## 👥 Equipe Plumo — CESAR School

| Nome | E-mail | Funções |
|------|--------|----------|
| **André Borges Viana** | abv2@cesar.school | Desenvolvedor • Verificação e Validação • Revisão textual |
| **Bruno Augusto da Rocha Leite Filho** | barlf@cesar.school | Desenvolvedor • Verificação e Validação • Gestor de Projetos |
| **Danilo Araújo Duleba** | dad@cesar.school | Desenvolvedor • Verificação e Validação |
| **Gustavo Torres Castro** | gtc@cesar.school | Desenvolvedor • Representante • Verificação e Validação |
| **Igor Gabriel Dutra Silva** | igds@cesar.school | Desenvolvedor • Designer • Verificação e Validação |
| **Maria Augusta Hatem da Fonte** | mahf@cesar.school | Desenvolvedora • Verificação e Validação • Revisão textual |
| **Mariana Maliu da Rocha Montarroyos** | mmrm@cesar.school | Desenvolvedora • Verificação e Validação • Revisão textual |
| **Karina Leal Almeida Peixoto** | klap@cesar.school | Designer • Gestora de Projetos |
| **Maria Mariana Barros Nascimento** | mmbn@cesar.school | Designer • Revisão textual |
| **Naiany de Oliveira Gama Jardim** | nogj@cesar.school | Designer |
| **Sofia Cunha Falcão** | scf@cesar.school | Designer |
| **Yasmin Espósito de Barros Correia** | yebc@cesar.school | Designer • Representante • Verificação e Validação |

---

## 📄 Licença
Projeto acadêmico — uso educacional e de pesquisa.  
© 2025 Equipe Plumo • CESAR School • Jornal do Commercio.
