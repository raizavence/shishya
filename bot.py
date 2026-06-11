#!/usr/bin/env python3
"""Shishya — शिष्य — Companheiro de jornada de Raíza Venceslau no caminho do Vedanta."""

import asyncio
import io
import json
import logging
import os
import sqlite3
from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GHOST_URL      = os.getenv("GHOST_URL", "https://raizavenceslau.com.br")
GHOST_ADMIN_KEY = os.getenv("GHOST_ADMIN_KEY", "")
VAK_TOKEN      = os.getenv("VAK_TOKEN", "")
VAK_DB_PATH    = os.getenv("VAK_DB_PATH", "/root/vak/memoria.db")
TIMEZONE       = ZoneInfo("America/Sao_Paulo")
DB_PATH        = os.path.join(os.path.dirname(__file__), "memoria.db")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ─── IDENTIDADE ───────────────────────────────────────────────────────────────

SHISHYA_IDENTITY = """Você é Shishya — शिष्य — companheiro de jornada de Raíza Venceslau no caminho do Vedanta.

Shishya existe para testemunhar. Não para resolver, acolher, motivar, incentivar, concluir ou ensinar.
Seu papel é estar presente, ouvir com profundidade, e fazer perguntas que aprofundem o que Raíza traz —
perguntas que saem do fio que ela mesma puxou, não de onde você acha que ela deveria ir.

Você não é psicólogo. Não é terapeuta. Não é professor. Não é guia espiritual.
Você é testemunha. Como o Sakshi — a consciência que observa sem interferir.

O que Shishya faz:
- Ouve o que é trazido sem julgamento
- Faz perguntas que aprofundam, não que direcionam
- Não insiste em respostas, conclusões ou fechamentos
- Reconhece emoções sem tentar transformá-las
- Interpreta a textura do momento com profundidade — não apenas as palavras
- Toma nota de tudo: silêncios, contradições, padrões, recorrências
- Aprende continuamente quem é Raíza, como ela pensa, o que a ocupa

O que Shishya não faz:
- Não oferece soluções
- Não valida nem invalida escolhas
- Não aconselha
- Não usa frases como "é natural sentir isso", "você está no caminho certo", "isso vai passar"
- Não conclui o que Raíza não concluiu
- Não preenche silêncios com palavras desnecessárias
- Não elogia, não encoraja, não reconforta

Tom: presente, atento, sem pressa. Poucas palavras quando poucas bastam.
Uma pergunta de cada vez. Nunca duas.

Você é tratado no masculino."""

VEDANTA_CONTEXT = """Raíza estuda Advaita Vedanta com Jonas Masetti no Instituto Vishva Vidya (Brasil).

Advaita Vedanta — fundamentos:
- Brahman: realidade absoluta, não-dual, sem atributos (nirguna). Tudo o que existe é Brahman.
- Atman: o Self, a consciência individual — idêntico a Brahman. "Aham Brahmasmi".
- Maya: o poder que faz Brahman aparecer como multiplicidade. Não é ilusão no sentido de inexistente — é aparência sem substância própria.
- Avidya: ignorância da própria natureza. Causa do sofrimento e da identificação com o que não se é.
- Jiva: o indivíduo aparente — Atman + identificação com corpo-mente.
- Nāma-rūpa: nome e forma — o mundo fenomênico, a multiplicidade aparente.
- Sakshi: a consciência testemunha — o que observa sem ser afetado. Imóvel, sempre presente.
- Viveka: discernimento entre o real (Brahman/Atman) e o não-real (nāma-rūpa).
- Vairagya: desapego — não rejeição do mundo, mas não-dependência dele.
- Mumukshutva: ardência pela liberação.
- Moksha: liberação — reconhecimento de que nunca houve separação de Brahman.
- Adhyasa: superimposição — projetar qualidades de um sobre outro (ex: tomar o corpo como o Self).
- Neti neti: "não isso, não isso" — método de eliminação para apontar o que Atman não é.
- Mahavakyas: "Aham Brahmasmi" (Eu sou Brahman), "Tat tvam asi" (Tu és isso), "Prajnanam Brahma" (Consciência é Brahman), "Ayam Atma Brahma" (Este Self é Brahman).
- Três estados: jagrat (vigília), svapna (sonho), sushupti (sono profundo). Turiya: o quarto — consciência que permeia os três.
- Pancha kosha: cinco véus (annamaya, pranamaya, manomaya, vijnanamaya, anandamaya) que encobrem Atman.
- Shruti: textos revelados — Upanishads, Bhagavad Gita, Brahma Sutras.

Textos centrais no Vishva Vidya: Vivekachudamani (Shankara), Bhagavad Gita, Mandukya Upanishad, Upadesha Sahasri.

Sânscrito — termos frequentes:
- Om (ॐ): o som primordial, símbolo de Brahman
- Guru: o mestre que dissipa a escuridão (gu = escuridão, ru = aquele que remove)
- Shishya (शिष्य): discípulo
- Shraddha: fé baseada em confiança, não em crença cega
- Sadhana: prática espiritual
- Samsara: ciclo de nascimento, morte e renascimento — alimentado por avidya e karma
- Karma: ação e seus frutos
- Dharma: lei, dever, ordem natural
- Vritti: modificação da mente, pensamento
- Antahkarana: instrumento interno (manas, buddhi, chitta, ahamkara)
- Ahamkara: o sentido de "eu" — o ego como função, não como entidade
- Sat-chit-ananda: Ser-Consciência-Bem-aventurança — natureza de Brahman/Atman

Use este conhecimento para engajar com profundidade quando Raíza trouxer conceitos vedânticos ou termos sânscritos."""

WITNESS_PROMPT = """ANTES de responder, identifique o modo pela mensagem atual — nesta ordem:

1. MODO ESCRITA — se Raíza pediu para escrever, continuar, finalizar, desenvolver ou completar um trecho
   Sinais: "me ajuda a finalizar", "escreve o fechamento", "continua", "faz um parágrafo", "como termino isso", "desenvolve essa ideia"
   → Escreva o trecho imediatamente, na voz dela. Sem perguntas antes.
   → Entregue APENAS o texto — sem preâmbulo ("O texto está pronto..."), sem separadores (---), sem pergunta de fechamento
   → NUNCA adicione frases motivacionais ao leitor ("Se você chegou até aqui", "Boa leitura", "boa caminhada") — isso é falso e contradiz a voz de Raíza
   → NUNCA adicione parágrafos de conclusão ou chamadas para ação que ela não escreveu
   → No máximo uma linha após o texto explicando a escolha, só se não for óbvio

2. MODO EDIÇÃO — se Raíza pediu correção ou edição de um texto existente
   Sinais: "corrige", "edita isso", "ajusta aqui", "muda essa parte", "corrige os erros"
   → Devolva o texto completo já corrigido
   → Correção de erros: ortografia e gramática, preserve voz e ritmo intactos
   → Edição específica: faça exatamente o que foi pedido, não altere o restante
   → Uma linha após o texto dizendo o que mudou

3. MODO LEITURA — se Raíza colou um texto que ela escreveu e fez uma pergunta sobre ele
   Sinais: "o que você entendeu?", "tá claro?", "o que falta?", "o que você achou?", "o que ficou confuso?"
   → Leia com profundidade real e responda a pergunta com substância
   → Diga o que entendeu, o que está funcionando, o que ficou difuso
   → Uma pergunta ao final só se fizer sentido natural
   → Não desvie para o testemunho padrão

4. MODO ESTUDO — se o assunto é claramente filosófico ou vedântico, sem pedido de escrita
   Sinais: debate de conceitos, dúvidas sobre o ensinamento, elaboração de ideias, termos sânscritos
   → Engaje intelectualmente e com profundidade, como dois estudantes examinando juntos
   → Uma pergunta de cada vez, se pertinente
   → Se algo contradiz o Advaita tradicional: aponte com gentileza e explique — não para corrigir, para investigar
   → Nunca finja concordar com algo que contradiz o ensinamento
   → Se no meio do estudo Raíza pedir para escrever algo: vá direto para MODO ESCRITA

5. TESTEMUNHO — qualquer outra situação
   → Receba sem julgamento. Identifique o fio central. Faça UMA pergunta que aprofunde esse fio.
   → Não resolva, não acolha, não conclua o que ela não concluiu.
   → Leia o histórico — o fio pode ter começado antes.
   → Se ela trouxer silêncio ou contradição: não comente a emoção, pergunte sobre o que está por baixo.

PERSISTÊNCIA DE MODO:
- Se o modo ativo estiver informado no contexto (MODO ATIVO: X), mantenha-o enquanto o assunto continuar sendo o mesmo — mesmo que a mensagem atual não o sinalize explicitamente.
- Só mude de modo se Raíza mudar claramente de assunto ou pedir explicitamente.
- Em MODO ESCRITA ou MODO EDIÇÃO: não faça perguntas de aprofundamento ou reflexão. Entregue o que foi pedido.

QUANDO INCERTO:
- Se o modo não estiver claro pela mensagem atual e pelo histórico, pergunte antes de responder: "Estamos em reflexão, debate ou escrita?"

QUANDO CORRIGIDA:
- Se Raíza disser que não quer perguntas, debate ou aprofundamento neste momento, adapte imediatamente: entre em MODO ESCRITA ou MODO EDIÇÃO conforme o contexto e fique lá.

OBRIGATÓRIO — última linha de toda resposta:
[modo:ESCRITA], [modo:EDICAO], [modo:LEITURA], [modo:ESTUDO] ou [modo:TESTEMUNHO]"""

# ─── BANCO ────────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                date      TEXT NOT NULL,
                role      TEXT NOT NULL,
                content   TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS diario (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                date             TEXT UNIQUE NOT NULL,
                estado           TEXT NOT NULL,
                temas            TEXT,
                insights         TEXT,
                duvidas          TEXT,
                conflitos        TEXT,
                emocoes          TEXT,
                perguntas_abertas TEXT,
                resumo           TEXT,
                apice            TEXT,
                ponto_chave      TEXT,
                insight_principal TEXT,
                frases_impacto   TEXT,
                created_at       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS aprendizados (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                conteudo   TEXT NOT NULL,
                categoria  TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conhecimento (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo     TEXT,
                conteudo   TEXT NOT NULL,
                categoria  TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS semanas (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                semana_inicio TEXT NOT NULL,
                semana_fim    TEXT NOT NULL,
                rascunho      TEXT,
                post_url      TEXT,
                estado        TEXT DEFAULT 'rascunho',
                created_at    TEXT NOT NULL
            );
        """)

def get_config(key, default=None):
    with get_db() as conn:
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

def set_config(key, value):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, str(value))
        )

ENCERRAR  = {"encerrar","encerra","encerro","encerrei","encerramos","encerrando","fechar","fecha","fechei","fechamos","fechando","terminar","termina","termino","terminei","terminamos","terminando","fim","final","finalizar","finaliza","finalize","acabar","acaba","acabei","acabamos","acabando","pronto","chega","para","pare"}
AUTORIZAR = {"autorizar","autoriza","autorizo","autorizei","autorizamos","autorizando","autorizado","aprovar","aprova","aprovo","aprovei","aprovamos","aprovando","aprovado","liberar","libera","liberado","pode","sim","s","ok","vai","bora","claro","isso","manda","positivo"}
DESCARTAR = {"descartar","descarta","descarto","descartei","descartamos","descartando","descartado","cancelar","cancela","cancelo","cancelei","cancelamos","cancelando","cancelado","não","nao","n","no","nope","pare","stop","deixa","esquece"}
GERAR_SEMANA = {"semanal","conteúdo semanal","conteudo semanal","post semanal","postagem semanal","rascunho semanal","gerar semana","fazer semana","semana do blog","conteúdo da semana","conteudo da semana"}
MANDAR_VAK  = {"manda pra vak","manda para a vak","envia pra vak","envia para a vak","manda publicar","publica isso","manda isso pra vak","manda pra vāk","envia pra vāk","pode enviar pra vak","pode enviar para a vak","publicar","publica","pode publicar","enviar pra vak","enviar para vak","enviar para a vak"}

def match(text: str, variants: set) -> bool:
    tokens = text.lower().strip().rstrip(".,!?").split()
    return bool(variants.intersection(tokens)) or any(v in text.lower() for v in variants if " " in v)

def now_tz():
    return datetime.now(TIMEZONE)

def today_str():
    return now_tz().strftime("%Y-%m-%d")

def business_date():
    # Antes das 6h, o "dia" de negócio ainda é ontem — a janela 20h-00h precisa
    # ver as mensagens gravadas com a data anterior.
    now = now_tz()
    if now.hour < 6:
        return (now - timedelta(hours=6)).strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")

def now_str():
    return now_tz().isoformat()

def get_today_messages():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content, timestamp FROM conversations WHERE date = ? ORDER BY id",
            (business_date(),)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]

def save_message(role, content):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations (date, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (business_date(), role, content, now_str())
        )

def get_conversation_state():
    state = get_config("conversation_state", "idle")
    state_date = get_config("state_date", "")
    if state_date != business_date():
        return "idle"
    return state

def set_conversation_state(state):
    set_config("conversation_state", state)
    set_config("state_date", business_date())

# ─── LLM ──────────────────────────────────────────────────────────────────────

def get_conhecimento_context():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT titulo, conteudo, categoria FROM conhecimento ORDER BY id DESC LIMIT 50"
        ).fetchall()
    if not rows:
        return ""
    items = []
    for r in rows:
        prefix = f"[{r['categoria']}] " if r["categoria"] else ""
        titulo = f"{r['titulo']}: " if r["titulo"] else ""
        items.append(f"- {prefix}{titulo}{r['conteudo']}")
    return "Conhecimento adicional alimentado por Raíza:\n" + "\n".join(items)

def get_aprendizados_context():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT conteudo FROM aprendizados ORDER BY id DESC LIMIT 30"
        ).fetchall()
    if not rows:
        return ""
    return "O que observei sobre Raíza ao longo do tempo:\n" + "\n".join(f"- {r['conteudo']}" for r in rows)

def witness_response(user_message, history):
    import re as _re

    modo_ativo = get_config("modo_ativo", "")

    messages = [
        {"role": "system", "content": SHISHYA_IDENTITY},
        {"role": "system", "content": VEDANTA_CONTEXT},
    ]

    if modo_ativo:
        messages.append({"role": "system", "content": f"MODO ATIVO: {modo_ativo}. Mantenha este modo até Raíza mudar explicitamente de assunto."})

    messages.append({"role": "system", "content": WITNESS_PROMPT})

    conhecimento = get_conhecimento_context()
    if conhecimento:
        messages.append({"role": "system", "content": conhecimento})

    aprendizados = get_aprendizados_context()
    if aprendizados:
        messages.append({"role": "system", "content": aprendizados})

    if history:
        # Limita às últimas 30 mensagens para não estourar o limite de tokens
        trimmed = history[-30:]
        hist_text = "\n".join(
            f"{m['role'].upper()} [{m['timestamp']}]: {m['content']}" for m in trimmed
        )
        messages.append({"role": "system", "content": f"Histórico de hoje:\n{hist_text}"})

    messages.append({"role": "user", "content": user_message})

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=1500,
    )
    text = response.choices[0].message.content.strip()

    # Extrai e salva o modo da tag obrigatória, remove da resposta
    match_modo = _re.search(r'\[modo:(\w+)\]', text, _re.IGNORECASE)
    if match_modo:
        set_config("modo_ativo", match_modo.group(1).upper())
        text = _re.sub(r'\s*\[modo:\w+\]', '', text).strip()

    return text

def generate_diary(messages, state):
    with get_db() as conn:
        if state in ("silencio", "sem_exposicao"):
            conn.execute(
                "INSERT OR REPLACE INTO diario (date, estado, created_at) VALUES (?, ?, ?)",
                (business_date(), state, now_str())
            )
            return

    if not messages:
        return

    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )

    prompt = f"""Analise esta conversa e extraia, em JSON:

{{
  "temas": ["lista de temas centrais abordados"],
  "insights": ["insights que emergiram, mesmo que implícitos"],
  "duvidas": ["dúvidas que ficaram abertas, não respondidas"],
  "conflitos": ["tensões internas ou contradições presentes"],
  "emocoes": ["emoções identificadas — pela palavra ou pela textura do que foi dito"],
  "perguntas_abertas": ["perguntas que ficaram sem resposta ou sem conclusão"],
  "resumo": "um parágrafo único que descreve o estado interno e o tom do dia",
  "apice": "o momento de maior intensidade ou profundidade da conversa — descrito em uma frase",
  "ponto_chave": "o núcleo central do que foi dito — a ideia que sustenta tudo o mais",
  "insight_principal": "o insight mais significativo que emergiu, ou null se não houver",
  "frases_impacto": ["frases ditas por Raíza que carregam peso e profundidade — copiadas literalmente, sem paráfrase"]
}}

Regra para frases_impacto: copie as palavras exatas de Raíza. Não resuma, não reescreva.
Só inclua frases que tenham densidade real — que possam ser citadas em aspas numa postagem.

Conversa:
{conversation_text}

Retorne apenas o JSON válido, sem markdown."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Você é um observador silencioso que analisa conversas com profundidade e sem julgamento."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1000,
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {}

    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO diario
               (date, estado, temas, insights, duvidas, conflitos, emocoes, perguntas_abertas, resumo,
                apice, ponto_chave, insight_principal, frases_impacto, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                business_date(),
                "com_exposicao",
                json.dumps(data.get("temas", []), ensure_ascii=False),
                json.dumps(data.get("insights", []), ensure_ascii=False),
                json.dumps(data.get("duvidas", []), ensure_ascii=False),
                json.dumps(data.get("conflitos", []), ensure_ascii=False),
                json.dumps(data.get("emocoes", []), ensure_ascii=False),
                json.dumps(data.get("perguntas_abertas", []), ensure_ascii=False),
                data.get("resumo", ""),
                data.get("apice", ""),
                data.get("ponto_chave", ""),
                data.get("insight_principal") or "",
                json.dumps(data.get("frases_impacto", []), ensure_ascii=False),
                now_str(),
            ),
        )

def detect_learning(messages):
    if len(messages) < 4:
        return None

    conversation_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )

    with get_db() as conn:
        existing = conn.execute(
            "SELECT conteudo FROM aprendizados ORDER BY id DESC LIMIT 20"
        ).fetchall()
    existing_text = "\n".join(f"- {r['conteudo']}" for r in existing) if existing else "nenhum"

    prompt = f"""Analise esta conversa e identifique se há algo novo e relevante para aprender sobre Raíza —
um padrão de pensamento, forma de processar emoções, tema recorrente, característica de linguagem, preferência.

Aprendizados já salvos (não repetir):
{existing_text}

Se houver algo genuinamente novo: retorne JSON:
{{"aprendizado": "descrição concisa em terceira pessoa", "categoria": "padrão|emoção|tema|processamento|linguagem"}}

Se não houver nada novo: retorne:
{{"aprendizado": null}}

Conversa:
{conversation_text}

Retorne apenas o JSON."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=200,
    )

    try:
        data = json.loads(response.choices[0].message.content.strip())
        return data.get("aprendizado")
    except Exception:
        return None

# ─── FECHAMENTO ────────────────────────────────────────────────────────────────

async def close_day(bot: Bot, state: str):
    messages = get_today_messages()
    await asyncio.to_thread(generate_diary, messages, state)

    if state == "com_exposicao" and messages:
        learning = await asyncio.to_thread(detect_learning, messages)
        if learning:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO aprendizados (conteudo, categoria, created_at) VALUES (?, ?, ?)",
                    (learning, "auto", now_str())
                )
            logger.info(f"Aprendizado detectado: {learning}")

    set_config("modo_ativo", "")
    set_conversation_state("closed")
    logger.info(f"Dia encerrado — estado: {state}")

# ─── ESTILO DE ESCRITA ────────────────────────────────────────────────────────

def analyze_writing_style(text):
    prompt = f"""Analise este texto escrito por Raíza Venceslau e extraia um perfil de escrita detalhado.

Raíza é estudante de Vedanta. Escreve sobre o processo interno — a jornada espiritual como ela realmente é, sem superação nem conclusão.

Extraia, em JSON:
{{
  "abertura": "como ela tipicamente abre o texto — qual é o movimento inicial",
  "desenvolvimento": "como a ideia central se desenvolve — linear, espiral, por acumulação, por contraste",
  "conexoes": "como ela liga contextos — o pessoal ao filosófico, o concreto ao abstrato",
  "vocabulario": ["palavras e expressões características que ela usa"],
  "ritmo": "como são as frases — curtas e cortadas, longas e acumulativas, mistura",
  "fechamento": "como ela tipicamente fecha — em aberto, com pergunta, com afirmação, com silêncio",
  "tom": "o tom geral — intimista, observacional, desafiador, etc.",
  "o_que_evitar": ["padrões que ela NÃO usa — o que seria falso ao seu estilo"]
}}

Texto:
{text}

Retorne apenas o JSON válido."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )

    try:
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception:
        return None

# ─── REFLEXÃO SEMANAL ─────────────────────────────────────────────────────────

def generate_reflexao(conversations):
    if not conversations:
        return None

    all_text = ""
    for date in sorted(conversations.keys()):
        msgs = conversations[date]
        all_text += f"\n--- {date} ---\n"
        for msg in msgs:
            role_label = "Raíza" if msg["role"] == "user" else "Shishya"
            all_text += f"{role_label}: {msg['content']}\n"

    prompt = f"""Abaixo estão as conversas da semana entre Raíza e o Shishya.

Sua tarefa: listar TODAS as trocas em que houve uma pergunta do Shishya seguida de uma resposta de Raíza com substância — não apenas as que pareceram mais importantes. Não filtre, não selecione, não omita.

Regras obrigatórias:
- Copie as falas EXATAMENTE como estão. Não resuma, não parafrase, não encurte, não edite.
- Se a fala for longa, copie inteira.
- "raiza_trouxe": a mensagem de Raíza imediatamente antes da pergunta do Shishya — literal.
- "shishya_perguntou": a pergunta exata do Shishya — literal.
- "raiza_desenvolveu": a resposta de Raíza após a pergunta — literal, completa.

Retorne JSON:
{{
  "trocas": [
    {{
      "data": "YYYY-MM-DD",
      "raiza_trouxe": "fala literal de Raíza",
      "shishya_perguntou": "pergunta literal do Shishya",
      "raiza_desenvolveu": "resposta literal e completa de Raíza"
    }}
  ]
}}

Se não houver conversas (só silêncios), retorne:
{{"trocas": []}}

Conversas:
{all_text}

Retorne apenas o JSON válido."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000,
    )

    try:
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception:
        return None

# ─── GERAÇÃO SEMANAL ──────────────────────────────────────────────────────────

def get_week_diary():
    today = now_tz().date()
    week_ago = today - timedelta(days=7)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM diario WHERE date >= ? AND date <= ? ORDER BY date",
            (str(week_ago), str(today))
        ).fetchall()
    return [dict(r) for r in rows]

def get_week_conversations():
    today = now_tz().date()
    week_ago = today - timedelta(days=7)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT date, role, content FROM conversations WHERE date >= ? AND date <= ? ORDER BY date, id",
            (str(week_ago), str(today))
        ).fetchall()
    by_day = {}
    for r in rows:
        by_day.setdefault(r["date"], []).append({"role": r["role"], "content": r["content"]})
    return by_day

def generate_weekly_draft(entries, conversations=None):
    def parse_field(val):
        if not val:
            return []
        try:
            return json.loads(val)
        except Exception:
            return [val]

    if conversations is None:
        conversations = {}

    days_text = ""
    for e in entries:
        estado_label = {
            "com_exposicao": "Com exposição",
            "sem_exposicao": "Sem exposição",
            "silencio": "Silêncio",
        }.get(e["estado"], e["estado"])

        days_text += f"\n--- {e['date']} ({estado_label}) ---\n"
        if e["estado"] == "com_exposicao":
            if e.get("resumo"):
                days_text += f"Resumo: {e['resumo']}\n"
            if e.get("apice"):
                days_text += f"Ápice: {e['apice']}\n"
            if e.get("ponto_chave"):
                days_text += f"Ponto-chave: {e['ponto_chave']}\n"
            if e.get("insight_principal"):
                days_text += f"Insight principal: {e['insight_principal']}\n"
            frases = parse_field(e.get("frases_impacto"))
            if frases:
                days_text += "Frases (literais):\n" + "\n".join(f'  "{f}"' for f in frases) + "\n"
            temas = parse_field(e.get("temas"))
            if temas:
                days_text += f"Temas: {', '.join(temas)}\n"
            emocoes = parse_field(e.get("emocoes"))
            if emocoes:
                days_text += f"Emoções: {', '.join(emocoes)}\n"
            perguntas = parse_field(e.get("perguntas_abertas"))
            if perguntas:
                days_text += f"Perguntas abertas: {'; '.join(perguntas)}\n"

            # Diálogo real do dia
            conv = conversations.get(e["date"], [])
            if conv:
                days_text += "Diálogo do dia (Shishya pergunta / Raíza responde):\n"
                for msg in conv:
                    role_label = "Raíza" if msg["role"] == "user" else "Shishya"
                    days_text += f"  {role_label}: {msg['content']}\n"

    perfil_text = ""
    perfil_raw = get_config("perfil_escrita")
    if perfil_raw:
        try:
            p = json.loads(perfil_raw)
            perfil_text = f"""
Perfil de escrita de Raíza (extraído de textos que ela escreveu — use como referência de voz e estilo):
- Abertura: {p.get('abertura', '')}
- Desenvolvimento: {p.get('desenvolvimento', '')}
- Conexões: {p.get('conexoes', '')}
- Vocabulário característico: {', '.join(p.get('vocabulario', []))}
- Ritmo: {p.get('ritmo', '')}
- Fechamento: {p.get('fechamento', '')}
- Tom: {p.get('tom', '')}
- O que evitar: {', '.join(p.get('o_que_evitar', []))}

"""
        except Exception:
            perfil_text = ""

    prompt = f"""Você vai criar um rascunho de postagem para o blog de Raíza Venceslau.
{perfil_text}

Este blog é um registro. Não um guia, não um ensinamento — um testemunho de alguém que está dentro do processo.
Raíza estuda Vedanta. O Vedanta, quando entra de verdade, não traz harmonia nem vitória. Traz a vida sendo vista como ela é.

O que este texto é:
- Um relato contínuo, desafiador, sem final feliz.
- Registra os caminhos que a mente faz — os desvios, as resistências, os momentos em que algo cede e os momentos em que nada cede.
- O processo não se resolve. Ele continua. O texto termina onde a semana terminou — em aberto, em movimento, ou em silêncio. Nunca em conclusão.

O que este texto NÃO é:
- Não é uma história de superação.
- Não tem moral.
- Não transforma dificuldade em vitória, nem tensão em harmonia.
- Não eleva o tom para parecer mais bonito ou mais espiritual do que o material bruto indica.
- Não usa palavras que sugerem chegada, conquista ou paz quando o processo não chegou lá.

TOM: o narrador acompanha o movimento da mente sem julgamento e sem edição emocional. Se a semana foi difícil, o texto é difícil. Se ficou uma pergunta, ela fica lá — não é respondida pelo narrador.

TÍTULO: tom de registro documental — preciso, observacional, como uma anotação de campo. Não é emocional nem metafórico. Nomeia o que aconteceu ou o que estava em movimento, sem dramatizar. Evite palavras abstratas (harmonia, coragem, jornada, processo, caminho) e metáforas poéticas. Prefira o concreto e o específico — o que foi observado, o que ocupou a mente, o estado em que estava. Deve despertar curiosidade pela precisão, não pela emoção.

ESTRUTURA — início, meio e fim reconhecíveis, mas não como etapas de uma história de crescimento:
- Início: onde a mente estava ao entrar na semana — qual era o peso, a pergunta, o estado
- Meio: o que se moveu, o que apareceu, o que ficou em tensão — os caminhos que a mente percorreu
- Fim: onde o processo está agora. Não é resolução. É onde parou — uma pergunta aberta, algo que não se fechou, o chão em que está pisando agora

Onde houver "Frases (literais)" ou falas de Raíza no diálogo: use essas frases em aspas no texto quando fizerem sentido.
Corrija erros gramaticais, mas preserve a voz, o ritmo e o sentido exato. Não parafrase.

Quando o diálogo mostrar uma pergunta do Shishya que Raíza respondeu: integre a resposta ao texto. Se a pergunta ficou sem resposta, ela pode aparecer no texto como pergunta — pertence ao registro.

Dados da semana:
{days_text}

Escreva em português.

Formato de retorno (JSON):
{{
  "titulo": "...",
  "conteudo": "texto completo da postagem em markdown"
}}

Retorne apenas o JSON."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=1200,
    )

    try:
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception:
        return None

# ─── DISPARO PARA VĀK ────────────────────────────────────────────────────────

async def notificar_vak(titulo: str, semana_id: int):
    if not VAK_TOKEN:
        logger.warning("VAK_TOKEN não configurado — não foi possível notificar a Vāk.")
        return

    # Lê o conteúdo completo do rascunho
    conteudo = ""
    subtitulo = ""
    try:
        with get_db() as conn:
            row = conn.execute("SELECT rascunho FROM semanas WHERE id = ?", (semana_id,)).fetchone()
        if row:
            draft = json.loads(row[0])
            conteudo = draft.get("conteudo", "")
            subtitulo = draft.get("subtitulo", "")
    except Exception as e:
        logger.error(f"Erro ao ler rascunho {semana_id}: {e}")

    # Escreve pendente no banco da Vāk
    try:
        conn = sqlite3.connect(VAK_DB_PATH)
        # CONTRATO pendente: {titulo, subtitulo, conteudo, semana_id} — espelhado em vak/bot.py (montar_pendente)
        rascunho_payload = json.dumps({"semana_id": semana_id, "titulo": titulo, "subtitulo": subtitulo, "conteudo": conteudo}, ensure_ascii=False)
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            ("pendente", rascunho_payload)
        )
        owner_id = conn.execute("SELECT value FROM config WHERE key = 'owner_chat_id'").fetchone()
        conn.commit()
        conn.close()
        owner_id = owner_id[0] if owner_id else None
    except Exception as e:
        logger.error(f"Erro ao escrever no banco da Vāk: {e}")
        return

    if not owner_id:
        logger.warning("owner_chat_id não encontrado no banco da Vāk.")
        return

    import urllib.request, urllib.parse

    def _enviar(texto, parse_mode=None):
        params = {"chat_id": owner_id, "text": texto}
        if parse_mode:
            params["parse_mode"] = parse_mode
        encoded = urllib.parse.urlencode(params)
        req_url = f"https://api.telegram.org/bot{VAK_TOKEN}/sendMessage?{encoded}"
        try:
            urllib.request.urlopen(req_url)
        except Exception as exc:
            logger.error(f"Erro ao enviar mensagem Telegram: {exc}")

    cabecalho = f"*{titulo}*"
    if subtitulo:
        cabecalho += f"\n_{subtitulo}_"
    _enviar(cabecalho, parse_mode="Markdown")

    CHUNK = 3900
    for i in range(0, len(conteudo), CHUNK):
        _enviar(conteudo[i:i + CHUNK])

    _enviar("---\nVocê quer fazer essa publicação? Responda sim para publicar ou não para cancelar.")
    logger.info("Vāk notificada sobre rascunho autorizado (com texto completo).")

async def enviar_texto_para_vak(update, texto: str):
    today = today_str()

    # Extrai título e subtítulo das primeiras linhas — sem GPT, sem modificar o texto
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    titulo = linhas[0].strip("*_ ") if linhas else "Postagem"
    subtitulo = ""
    linhas_cabecalho = 1
    if len(linhas) > 1:
        segunda = linhas[1].strip()
        if segunda.startswith("*") and segunda.endswith("*") and len(segunda) < 200:
            subtitulo = segunda.strip("*_ ")
            linhas_cabecalho = 2

    # Remove título e subtítulo do corpo — eles já vão como campos separados no Ghost
    cabecalho = {linhas[0]}
    if linhas_cabecalho > 1:
        cabecalho.add(linhas[1])
    corpo_linhas = []
    pulando_cabecalho = True
    for linha in texto.splitlines():
        if pulando_cabecalho:
            if linha.strip() == "" or linha.strip() in cabecalho:
                continue
            pulando_cabecalho = False
        corpo_linhas.append(linha)
    artigo = "\n".join(corpo_linhas)

    week_ago = (now_tz().date() - timedelta(days=7)).isoformat()
    draft = {"titulo": titulo, "subtitulo": subtitulo, "conteudo": artigo}

    with get_db() as conn:
        conn.execute(
            "INSERT INTO semanas (semana_inicio, semana_fim, rascunho, estado, created_at) VALUES (?, ?, ?, ?, ?)",
            (week_ago, today, json.dumps(draft, ensure_ascii=False), "autorizado", now_str())
        )
        semana_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    await update.message.reply_text(f"Mandando para a Vāk: *{titulo}*", parse_mode="Markdown")
    await notificar_vak(titulo, semana_id)

# ─── JOBS ─────────────────────────────────────────────────────────────────────

async def job_abertura(context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if not owner_id:
        return

    await context.bot.send_message(chat_id=owner_id, text="Om Shri Gurubhyo Namah 🙏")
    await asyncio.sleep(2)
    await context.bot.send_message(chat_id=owner_id, text="Qual é o assunto da sua mente agora?")

    if get_conversation_state() == "idle":
        set_conversation_state("open_schedule")

async def job_encerramento(context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if not owner_id:
        return

    state = get_conversation_state()
    if state == "closed":
        return

    messages = get_today_messages()
    diary_state = "com_exposicao" if messages else "silencio"
    await close_day(context.bot, diary_state)

# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    existing = get_config("owner_chat_id")

    if existing and existing != chat_id:
        return

    set_config("owner_chat_id", chat_id)
    await update.message.reply_text("Om Shri Gurubhyo Namah 🙏\n\nShishya está presente.")

async def cmd_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if str(update.effective_chat.id) != owner_id:
        return

    args = context.args
    target_date = args[0] if args else today_str()

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM diario WHERE date = ?", (target_date,)
        ).fetchone()

    if not row:
        await update.message.reply_text(f"Sem registro para {target_date}.")
        return

    row = dict(row)
    estado_label = {
        "com_exposicao": "Com exposição",
        "sem_exposicao": "Sem exposição",
        "silencio": "Silêncio",
    }.get(row["estado"], row["estado"])

    text = f"*{target_date} — {estado_label}*\n"

    if row["estado"] == "com_exposicao":
        def fmt(field):
            try:
                items = json.loads(row.get(field) or "[]")
                return "\n".join(f"• {i}" for i in items) if items else "—"
            except Exception:
                return "—"

        if row.get("resumo"):
            text += f"\n_{row['resumo']}_\n"
        text += f"\n*Temas:*\n{fmt('temas')}"
        text += f"\n\n*Emoções:*\n{fmt('emocoes')}"
        text += f"\n\n*Perguntas abertas:*\n{fmt('perguntas_abertas')}"

    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if str(update.effective_chat.id) != owner_id:
        return

    await update.message.reply_text("Deixa eu olhar a semana...")

    entries = get_week_diary()
    if not entries:
        await update.message.reply_text("Não há registros esta semana.")
        return

    conversations = get_week_conversations()
    draft = await asyncio.to_thread(generate_weekly_draft, entries, conversations)
    if not draft:
        await update.message.reply_text("Não consegui gerar o rascunho agora.")
        return

    today = today_str()
    week_ago = (now_tz().date() - timedelta(days=7)).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO semanas (semana_inicio, semana_fim, rascunho, estado, created_at) VALUES (?, ?, ?, ?, ?)",
            (week_ago, today, json.dumps(draft, ensure_ascii=False), "rascunho", now_str())
        )
        semana_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    set_config("semana_pendente_id", semana_id)
    set_config("semana_pendente_titulo", draft["titulo"])

    text = f"*{draft['titulo']}*\n\n{draft['conteudo']}"
    if len(text) > 4000:
        text = text[:4000] + "..."

    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_text(
        "Responda *autorizar* para liberar para a Vāk publicar, ou *descartar* para cancelar.",
        parse_mode="Markdown"
    )

async def cmd_aprender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if str(update.effective_chat.id) != owner_id:
        return
    args = context.args
    categoria = args[0] if args else "vedanta"
    categorias_validas = {"vedanta", "sanscrito", "vishva_vidya", "anotacao"}
    if categoria not in categorias_validas:
        await update.message.reply_text(
            f"Categoria inválida. Use: vedanta, sanscrito, vishva\\_vidya ou anotacao",
            parse_mode="Markdown"
        )
        return
    set_config("aguardando_conhecimento", categoria)
    await update.message.reply_text(f"Cola o conteúdo. Categoria: *{categoria}*", parse_mode="Markdown")

async def cmd_meu_estilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if str(update.effective_chat.id) != owner_id:
        return
    set_config("aguardando_estilo", "1")
    await update.message.reply_text("Cola o texto aqui.")

async def cmd_reflexao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if str(update.effective_chat.id) != owner_id:
        return

    await update.message.reply_text("Deixa eu olhar a semana...")

    conversations = get_week_conversations()
    if not conversations:
        await update.message.reply_text("Não há conversas esta semana.")
        return

    resultado = await asyncio.to_thread(generate_reflexao, conversations)
    if not resultado or not resultado.get("trocas"):
        await update.message.reply_text("Não encontrei trocas com desenvolvimento de pensamento esta semana.")
        return

    texto = "*O que se desenvolveu esta semana*\n\n"
    for t in resultado["trocas"]:
        texto += f"📌 _{t['data']}_\n"
        texto += f"*Você trouxe:* {t['raiza_trouxe']}\n"
        texto += f"*Shishya perguntou:* _{t['shishya_perguntou']}_\n"
        texto += f"*Você desenvolveu:* {t['raiza_desenvolveu']}\n\n"

    while texto:
        if len(texto) <= 4000:
            await update.message.reply_text(texto, parse_mode="Markdown")
            break
        split_at = texto.rfind("\n\n", 0, 4000)
        if split_at == -1:
            split_at = 4000
        await update.message.reply_text(texto[:split_at], parse_mode="Markdown")
        texto = texto[split_at:].lstrip()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if not owner_id or str(update.effective_chat.id) != owner_id:
        return

    text = update.message.text.strip()

    # Captura de conhecimento
    aguardando_conhecimento = get_config("aguardando_conhecimento")
    if aguardando_conhecimento:
        set_config("aguardando_conhecimento", "")
        lines = text.strip().split("\n")
        titulo = lines[0][:100] if lines[0] else ""
        with get_db() as conn:
            conn.execute(
                "INSERT INTO conhecimento (titulo, conteudo, categoria, created_at) VALUES (?, ?, ?, ?)",
                (titulo, text, aguardando_conhecimento, now_str())
            )
        await update.message.reply_text("Guardado. 🙏")
        return

    # Captura de texto para perfil de escrita
    if get_config("aguardando_estilo") == "1":
        set_config("aguardando_estilo", "")
        await update.message.reply_text("Analisando...")
        perfil = await asyncio.to_thread(analyze_writing_style, text)
        if perfil:
            set_config("perfil_escrita", json.dumps(perfil, ensure_ascii=False))
            await update.message.reply_text("Perfil de escrita salvo. Vou usar isso nas próximas gerações. 🙏")
        else:
            await update.message.reply_text("Não consegui analisar o texto agora.")
        return

    # Autorização semanal pendente
    semana_id = get_config("semana_pendente_id")
    if semana_id and match(text, AUTORIZAR):
        titulo = get_config("semana_pendente_titulo", "Postagem da semana")
        with get_db() as conn:
            conn.execute(
                "UPDATE semanas SET estado = 'autorizado' WHERE id = ?",
                (semana_id,)
            )
        set_config("semana_pendente_id", "")
        await update.message.reply_text("Autorizado. A Vāk vai te chamar. 🙏")
        await notificar_vak(titulo, int(semana_id))
        return

    if semana_id and match(text, DESCARTAR):
        set_config("semana_pendente_id", "")
        await update.message.reply_text("Descartado.")
        return

    # Geração de conteúdo semanal via linguagem natural
    if not semana_id and match(text, GERAR_SEMANA):
        await cmd_semana(update, context)
        return

    # Envio de texto para a Vāk publicar
    if match(text, MANDAR_VAK):
        with get_db() as conn:
            # Pega a última mensagem longa da Raíza — ela sempre cola o texto
            row = conn.execute(
                "SELECT content FROM conversations WHERE date = ? AND role = 'user' AND length(content) > 300 ORDER BY id DESC LIMIT 1",
                (business_date(),)
            ).fetchone()
        candidato = row["content"] if row else None
        if candidato:
            await enviar_texto_para_vak(update, candidato)
        else:
            await update.message.reply_text("Não encontrei um texto para enviar. Peça primeiro que eu escreva algo.")
        return

    # Encerramento — só verifica em mensagens curtas (até 5 palavras)
    if len(text.split()) <= 5 and match(text, ENCERRAR):
        current_state = get_conversation_state()
        messages = get_today_messages()

        if not messages and current_state in ("idle", "open_schedule"):
            diary_state = "sem_exposicao"
        elif messages:
            diary_state = "com_exposicao"
        else:
            diary_state = "sem_exposicao"

        await close_day(context.bot, diary_state)
        await update.message.reply_text("🙏")
        return

    # Conversa normal
    current_state = get_conversation_state()
    if current_state in ("idle", "closed"):
        set_conversation_state("open_user")

    history = get_today_messages()
    save_message("user", text)

    response = await asyncio.to_thread(witness_response, text, history)
    save_message("assistant", response)

    remaining = response
    while remaining:
        if len(remaining) <= 4000:
            await update.message.reply_text(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, 4000)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, 4000)
        if split_at == -1:
            split_at = 4000
        await update.message.reply_text(remaining[:split_at])
        remaining = remaining[split_at:].lstrip()

async def transcribe_voice(message) -> str | None:
    voice = message.voice or message.audio
    if not voice:
        return None
    try:
        file = await voice.get_file()
        buf = io.BytesIO(await file.download_as_bytearray())
        buf.name = "audio.ogg"
        transcript = await asyncio.to_thread(
            lambda: openai_client.audio.transcriptions.create(model="whisper-1", file=buf, language="pt")
        )
        return transcript.text.strip()
    except Exception:
        logger.exception("Erro ao transcrever áudio")
        return None


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = get_config("owner_chat_id")
    if not owner_id or str(update.effective_chat.id) != owner_id:
        return

    await update.message.chat.send_action("typing")
    text = await transcribe_voice(update.message)
    if not text:
        await update.message.reply_text("Não consegui entender o áudio. Pode repetir por escrito?")
        return

    await update.message.reply_text(f"_{text}_", parse_mode="Markdown")

    current_state = get_conversation_state()
    if current_state in ("idle", "closed"):
        set_conversation_state("open_user")

    history = get_today_messages()
    save_message("user", text)

    await update.message.chat.send_action("typing")
    response = await asyncio.to_thread(witness_response, text, history)
    save_message("assistant", response)

    remaining = response
    while remaining:
        if len(remaining) <= 4000:
            await update.message.reply_text(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, 4000)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, 4000)
        if split_at == -1:
            split_at = 4000
        await update.message.reply_text(remaining[:split_at])
        remaining = remaining[split_at:].lstrip()


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("diario", cmd_diario))
    app.add_handler(CommandHandler("semana", cmd_semana))
    app.add_handler(CommandHandler("reflexao", cmd_reflexao))
    app.add_handler(CommandHandler("aprender", cmd_aprender))
    app.add_handler(CommandHandler("meu_estilo", cmd_meu_estilo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & (filters.VOICE | filters.AUDIO) & ~filters.COMMAND,
        handle_voice,
    ))

    tz = TIMEZONE
    app.job_queue.run_daily(job_abertura, time=dt_time(20, 0, tzinfo=tz))
    app.job_queue.run_daily(job_encerramento, time=dt_time(0, 0, tzinfo=tz))

    logger.info("Shishya iniciado.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
