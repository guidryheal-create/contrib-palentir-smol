# Palentir OSINT  
**Advanced Multi-Agent Intelligence & OSINT Platform**

![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Status](https://img.shields.io/badge/status-active-success)

**Palentir OSINT** is a comprehensive reconnaissance and intelligence platform designed for investigative journalists, security researchers, and intelligence professionals.  
It automates company intelligence gathering using coordinated AI agents, constructs knowledge graphs with Neo4j, and delivers verifiable insights through a RAG-powered QA system.

---

## Table of Contents

- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Agent System](#agent-system)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Docker & Services](#docker--services)
- [Database Management](#database-management)
- [Security](#security)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

## Key Features

- **Multi-Agent Workforce** – CAMEL-AI powered agents operating in parallel  
- **Knowledge Graph** – Neo4j-based entity and relationship mapping  
- **Long-Term Memory** – Vector persistence using Qdrant  
- **RAG QA System** – Evidence-based question answering  
- **MCP Integration** – Extensible tooling via Model Context Protocol  
- **Real-Time Updates** – WebSocket task progress streaming  
- **Security-First** – OAuth2, rate limiting, XSS/CSRF protection  
- **Scalable by Design** – Docker Compose for local dev, Kubernetes-ready

---

## Architecture Overview

```

User → Frontend (Streamlit)
→ API (FastAPI)
→ Workforce Orchestrator
→ AI Agents (OSINT, Analysis, Verification)
→ Tools (MCP)
→ External OSINT APIs
→ Neo4j (Knowledge Graph)
→ PostgreSQL (Tasks, Metadata)
→ Qdrant (Vector Memory)
→ Redis (Caching & Queues)

````

---

## Prerequisites

- Python **3.11+**
- Docker & Docker Compose
- OpenAI API key
- **uv** package manager (auto-installed)

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/palentir-osint/palentir-osint.git
cd palentir-osint
````

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### 3. Start the Platform

#### Option A – Docker Compose (Recommended)

```bash
docker-compose up -d
```

**Services**

| Service  | URL                                            |
| -------- | ---------------------------------------------- |
| API      | [http://localhost:8000](http://localhost:8000) |
| Frontend | [http://localhost:8501](http://localhost:8501) |
| Neo4j    | [http://localhost:7474](http://localhost:7474) |
| Qdrant   | [http://localhost:6333](http://localhost:6333) |

#### Option B – Local Development

```bash
uv sync

python main.py api --reload
python main.py frontend
```

---

## Project Structure

```
palentir-osint/
├── src/
│   ├── agents/        # AI agents
│   ├── workforce/    # Task orchestration
│   ├── rag/           # Retrieval-Augmented QA
│   ├── api/           # FastAPI backend
│   ├── frontend/      # Streamlit UI
│   ├── toolkits/      # MCP tools
│   ├── services/      # DB & infrastructure
│   ├── models/        # Pydantic models
│   ├── config/        # Configuration
│   └── utils/         # Shared utilities
├── tests/
├── docs/
├── scripts/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── main.py            # CLI entry point
```

---

## Agent System

Specialized agents include:

* Task Orchestrator
* Network Analyzer (DNS, WHOIS, IPs)
* News & Media Searcher
* Social Intelligence Agent
* HR & Organization Mapper
* Technology Stack Detector
* Knowledge Graph Builder
* Memory Agent (Vector Store)
* Fact Verifier (RAG-based)

Agents collaborate through a shared task graph and persistent memory layer.

---

## Configuration

### Core Environment Variables

```bash
# LLM
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4-turbo

# Databases
NEO4J_URI=bolt://localhost:7687
POSTGRES_HOST=localhost
REDIS_HOST=localhost
QDRANT_HOST=localhost

# OSINT APIs
SHODAN_API_KEY=...
CENSYS_API_ID=...
TWITTER_BEARER_TOKEN=...
```

See `.env.example` for the full list.

---

## API Documentation

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Testing

```bash
python main.py test
pytest tests/test_agents.py -v
pytest tests/ --cov=src --cov-report=html
```

---

## Docker & Services

```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
docker-compose build --no-cache
docker-compose exec api bash
```

---

## Database Management

### Neo4j

```cypher
MATCH (n) RETURN n LIMIT 10;
MATCH (c:Company)-[r]->(e) RETURN c, r, e;
```

Default credentials: `neo4j / osint_password`

### PostgreSQL

```bash
psql -h localhost -U osint_user -d palentir_osint
```

---

## Security

* OAuth 2.0 authentication
* Role-based access control
* Input validation (Pydantic)
* Rate limiting & abuse protection
* Encrypted secrets and tokens

---

## Development Guide

### Code Quality

```bash
black src/
isort src/
flake8 src/
pylint src/
mypy src/
```

### Extending the Platform

**Add an Agent**

1. Implement agent in `src/agents/`
2. Register in workforce manager
3. Define capabilities
4. Add tests

**Add a Tool**

1. Create wrapper in `src/toolkits/`
2. Implement MCP interface
3. Register tool
4. Assign to agents

---

## Deployment

Production deployment guides are available in `docs/DEPLOYMENT.md`, including:

* Kubernetes manifests
* Cloud provider setups
* Monitoring & logging
* Performance tuning

CI/CD pipelines are provided via GitHub Actions.

---

## Documentation

* Architecture – `docs/ARCHITECTURE.md`
* API Reference – `docs/API.md`
* Agents – `docs/AGENTS.md`
* Setup – `docs/SETUP.md`
* Deployment – `docs/DEPLOYMENT.md`

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a pull request

All contributions are welcome.

---

## License

Apache License 2.0
See `LICENSE` for details.

---

## Disclaimer

This tool is intended **only for authorized security research and lawful investigations**.
Users are responsible for complying with all applicable laws and regulations.

---

**Built with ❤️ for investigators, analysts, and security researchers**

```
This is already solid enough to look “serious-project-energy” on GitHub.
```
