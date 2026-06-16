# Shishya — Companheiro de Jornada

Bot Telegram de testemunho diário para uma estudante de Vedanta. — शिष्य —

Recebe relatos do processo de estudo, faz perguntas que aprofundam o que foi trazido e documenta a jornada ao longo do tempo. Também transforma esses registros em postagens para o blog, descritivas e poéticas, sobre as etapas do caminho.

Não aconselha, não resolve, não guia. É testemunha.

---

## Tecnologias

- Python 3.10+
- python-telegram-bot
- OpenAI GPT-4o
- SQLite (memória de longo prazo)

## Configuração

Copie `.env.example` para `.env` e preencha:

```
TELEGRAM_TOKEN=
OPENAI_API_KEY=
```

## Execução

```bash
pip install -r requirements.txt
python bot.py
```

Ou via systemd: `sudo systemctl start shishya`
