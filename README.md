# Backup AI Monitor

Sistema em Python para monitoramento inteligente de logs em tempo real.

O projeto observa um arquivo de logs, identifica eventos suspeitos, classifica a severidade e gera relatorios automaticos com apoio de IA local via Ollama. A versao atual tambem possui uma primeira integracao com RAG e grafo local de dependencias para enriquecer analises de incidentes mais graves.

## Objetivo

O objetivo do projeto e ajudar na deteccao e analise de incidentes a partir de logs.

O sistema gera relatorios com:

- descricao do problema;
- possivel causa;
- nivel de severidade;
- evidencias encontradas nos logs;
- recomendacao de solucao;
- complemento gerado por IA local.

## Como Funciona

Fluxo principal:

```text
logs.txt
-> watcher.py
-> fila de analise
-> analyzer.py
-> relatorio local
-> Ollama
-> reports.jsonl
```

Para eventos de severidade alta ou critica, o sistema tambem tenta enriquecer o prompt da IA:

```text
Log de alta severidade
-> busca em PDFs internos com RAG
-> consulta grafo local de dependencias
-> prompt enriquecido
-> Ollama
-> relatorio final
```

Para eventos de baixa severidade, o fluxo continua simples e rapido, sem executar RAG.

## Estrutura Do Projeto

```text
backup-ai-monitor/
  analyzer.py              # Classifica logs, monta prompt e gera relatorio
  watcher.py               # Monitora logs.txt em tempo real
  generator.py             # Gera logs simulados para teste
  test_analyzer.py         # Testes unitarios da analise local

  rag_pdf_loader.py        # Extrai texto de PDFs
  rag_text_splitter.py     # Divide textos em trechos menores
  rag_embeddings.py        # Gera embeddings semanticos
  rag_vector_store.py      # Armazena e consulta embeddings no ChromaDB
  rag_retriever.py         # Busca trechos relevantes dos documentos
  enriched_context.py      # Junta contexto RAG + grafo
  ingest_documents.py      # Ingestao manual dos PDFs internos

  graph/
    dependency_graph.py    # Busca dependencias no grafo local
    components.json        # Componentes e relacoes do sistema

  docs/
    internal_pdfs/         # PDFs internos usados pelo RAG

  requirements.txt
```

## Requisitos

- Python 3.11 ou superior
- Ollama instalado localmente
- Um modelo baixado no Ollama, por exemplo:

```powershell
ollama pull llama3.2:1b
```

## Instalacao

Crie e ative o ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Instale as dependencias:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt --timeout 300 --retries 10 --prefer-binary
```

Se a instalacao falhar por timeout, instale em partes:

```powershell
.\venv\Scripts\python.exe -m pip install watchdog ollama
.\venv\Scripts\python.exe -m pip install pymupdf
.\venv\Scripts\python.exe -m pip install chromadb
.\venv\Scripts\python.exe -m pip install sentence-transformers
```

## Como Rodar

Execute o monitor:

```powershell
.\venv\Scripts\python.exe watcher.py
```

O sistema vai:

- iniciar o watcher;
- analisar logs existentes;
- iniciar o gerador de logs simulados;
- salvar relatorios em `reports.jsonl`.

## Como Testar Manualmente

Com o watcher rodando, adicione uma linha em `logs.txt`:

```text
[2026-07-01 10:02:00] DATABASE_ERROR backup-api ERROR database connection refused
```

Esse evento deve ser classificado como alta severidade e pode acionar o contexto enriquecido com RAG e grafo local.

Outro exemplo:

```text
[2026-07-01 10:01:00] UNAUTHORIZED_ACCESS /admin-panel
```

## RAG Com PDFs Internos

Coloque os PDFs dentro da pasta:

```text
docs/internal_pdfs/
```

Exemplos de PDFs uteis:

- arquitetura do sistema;
- documentacao de servicos;
- procedimentos de incidente;
- runbooks operacionais;
- documentacao de banco de dados e infraestrutura.

Depois rode a ingestao:

```powershell
.\venv\Scripts\python.exe ingest_documents.py
```

O script extrai o texto dos PDFs, divide em trechos, gera embeddings e salva no ChromaDB local em `data/chroma/`.

## Grafo Local De Dependencias

O grafo fica em:

```text
graph/components.json
```

Exemplo atual:

```text
Backup API -> DEPENDS_ON -> PostgreSQL Principal
```

Esse arquivo pode ser editado para adicionar novos servicos, bancos, servidores e relacoes.

Exemplo de relacoes possiveis:

```text
Service -> DEPENDS_ON -> Database
Service -> RUNS_ON -> Server
Server -> CONNECTED_TO -> Storage
```

## Testes

Rode os testes unitarios:

```powershell
.\venv\Scripts\python.exe -m unittest -v test_analyzer.py
```

## Arquivos Gerados Localmente

Estes arquivos e pastas nao devem ser enviados para o GitHub:

- `venv/`
- `__pycache__/`
- `logs.txt`
- `reports.jsonl`
- `data/chroma/`

Eles sao ignorados pelo `.gitignore`.

## Estado Atual

O projeto ja possui:

- monitoramento em tempo real;
- fila para analise sem travar o watcher;
- classificacao local de severidade;
- relatorio automatico em JSONL;
- integracao com Ollama;
- pipeline inicial de RAG;
- grafo local de dependencias;
- fallback caso RAG, grafo ou IA estejam indisponiveis.

## Proximos Passos

- Adicionar PDFs reais de documentacao interna;
- Expandir `graph/components.json` com mais componentes;
- Criar mais testes para RAG e grafo;
- Melhorar o formato final dos relatorios;
- Futuramente avaliar uso de Neo4j para um grafo mais robusto.
