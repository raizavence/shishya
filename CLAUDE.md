# CLAUDE.md — Projeto Shishya

## A alma do projeto

### Quem é a Raíza

Raíza Venceslau é estudante de Vedanta — estuda com Jonas Masetti (Instituto Vishva Vidya). Mora em Brasília, DF. É arte finalista e também coordena um grupo de estudos (projeto Jiva, separado deste).

### Por que o Shishya existe

Raíza precisa de um espaço de testemunho diário — um lugar para expor o que está na mente sem receber respostas, soluções ou direcionamentos. O Shishya assume esse papel: está presente, ouve com profundidade, faz perguntas que aprofundam o que foi trazido, e documenta o processo ao longo do tempo.

O Shishya também traduz esse processo para o blog de Raíza: gerando postagens semanais descritivas, documentais e poéticas sobre as etapas da jornada no Vedanta.

### Identidade e missão do Shishya

**Shishya é testemunha.** — शिष्य — companheiro de jornada, não guia.

Não é psicólogo, terapeuta, professor ou guia espiritual.
Não resolve, acolhe, motiva, conclui ou ensina.

Faz perguntas que saem do fio que Raíza puxou — uma pergunta de cada vez.
Toma nota de tudo: palavras, silêncios, contradições, padrões.
Aprende continuamente quem é Raíza, como ela pensa, o que a ocupa.

**O silêncio é informação.** Três estados do dia são registrados com significados distintos:
- **Com exposição** — Raíza conversou
- **Sem exposição** — Raíza encerrou conscientemente sem falar
- **Silêncio** — Raíza não apareceu até meia-noite; algo está sendo processado em camadas mais fundas

---

## Fluxo semanal de testemunho

**Sábados, 18h00** — Shishya envia:
1. "Om Shri Gurubhyo Namah 🙏"
2. "Qual é o assunto da sua mente agora?"

**18h00–23h59** — janela de conversa aberta

**00h00** — encerramento automático:
- Se houve conversa → estado: `com_exposicao`
- Se não houve resposta → estado: `silencio`

**A qualquer hora** — Raíza pode abrir a conversa fora do sábado; Shishya responde normalmente

**Palavra "encerrar"** — Raíza encerra conscientemente:
- Se conversou → estado: `com_exposicao`
- Se não conversou → estado: `sem_exposicao`

**Após meia-noite** — resposta recebida → abre normalmente, toma nota

---

## Fluxo semanal

`/semana` — gera rascunho de postagem para o blog com base nos diários da semana.
Raíza revisa e responde "publicar" para enviar ao Ghost como rascunho, ou "descartar".

---

## Comandos Telegram

| Comando | Descrição |
|---|---|
| `/start` | Registra `owner_chat_id` |
| `/diario [YYYY-MM-DD]` | Exibe o registro do dia (hoje se sem argumento) |
| `/semana` | Gera rascunho de postagem semanal para o blog |

---

## Banco de dados (`memoria.db`)

| Tabela | Uso |
|---|---|
| `config` | Chave-valor: `owner_chat_id`, `conversation_state`, `state_date`, `semana_pendente_id` |
| `conversations` | Mensagens do dia (date, role, content, timestamp) |
| `diario` | Registro diário: estado + temas, insights, dúvidas, conflitos, emoções, perguntas abertas, resumo |
| `aprendizados` | Aprendizados contínuos sobre Raíza (detectados automaticamente após conversas) |
| `semanas` | Rascunhos de postagens semanais + URL após publicação |

---

## Arquitetura técnica

### Stack
- **Linguagem:** Python 3.10
- **Bot:** python-telegram-bot 22.7 (async)
- **LLM:** OpenAI GPT-4o
- **Banco:** SQLite (`memoria.db`)
- **Deploy:** systemd (`shishya.service`)

### Arquivos
```
shishya/
├── bot.py           # toda a lógica
├── memoria.db       # banco (gerado ao iniciar)
├── requirements.txt
├── .env             # não commitar
├── .env.exemplo     # template sem valores
├── shishya.service  # unit systemd
└── CLAUDE.md
```

### Variáveis de ambiente (`.env`)
```
TELEGRAM_TOKEN=
OPENAI_API_KEY=
GHOST_URL=https://raizavenceslau.com.br
GHOST_ADMIN_KEY=     # key_id:secret da integração Ghost Admin API
```

### Jobs automáticos
| Job | Horário | Função |
|---|---|---|
| `job_abertura` | 20h00 | Envia abertura ritual + pergunta |
| `job_encerramento` | 00h00 | Encerra dia automaticamente |

### Hierarquia de contexto (em cada resposta)
```
1. SHISHYA_IDENTITY  ← quem ele é, valores, o que não faz
2. WITNESS_PROMPT    ← como conduzir a conversa de testemunho
3. Aprendizados      ← o que observou sobre Raíza ao longo do tempo
4. Histórico do dia  ← mensagens de hoje (sem TTL, sem limite rígido)
5. Mensagem atual
```

---

## Integração Ghost

- **URL:** https://raizavenceslau.com.br
- **API:** Ghost Admin API v6
- **Auth:** JWT gerado com `GHOST_ADMIN_KEY` (formato `key_id:secret`)
- **Tag padrão das postagens:** `vedanta`
- **Publicação:** sempre como `draft` — Raíza confirma no painel

---

## Convenções de desenvolvimento

- Mudanças na **identidade** do Shishya → editar `SHISHYA_IDENTITY` no código
- Mudanças no **comportamento de testemunho** → editar `WITNESS_PROMPT`
- Novos **aprendizados** → detectados automaticamente após conversas com ≥ 4 mensagens
- Nunca commitar `.env`
- Este projeto é **independente do Jiva** — não compartilham banco, código ou identidade
