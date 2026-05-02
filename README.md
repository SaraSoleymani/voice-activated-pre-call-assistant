# Voice-Activated-Pre-Call Assistant

A voice-activated pre-call intelligence tool for enterprise sales reps, built with Claude, MCP, and ElevenLabs.

Part of the **Building with Agentic AI** series — Article 9: MCP: How Agents Connect to the World.

Read the full article on [Medium](https://sarasoleymani.medium.com/) | Follow the series on [LinkedIn](https://www.linkedin.com/in/sarasoleymani/)

---

## What It Does

Ask a question out loud before a sales call. The assistant pulls live context from Gmail and Google Drive through MCP, synthesizes a structured pre-call brief with Claude, and reads it back to you through ElevenLabs.

**Example query:** *"Prep me for my 2pm call with ClientA"*

**Output:**
- Deal status, stage, and competing vendor
- Recent email context and any unanswered commitments
- Open questions from prior calls
- Flagged risks that need attention before this call

---

## Architecture

```
Mic Input
   ↓
ElevenLabs STT  (speech to text)
   ↓
FastAPI Backend
   ↓
Claude (claude-sonnet-4-6) + MCP
   ├── Google Drive MCP  →  account briefs, meeting notes, deal docs
   └── Gmail MCP         →  recent email threads, flagged action items
   ↓
Structured Pre-Call Brief
   ↓
ElevenLabs TTS  (text to speech)  +  Text Display on Screen
```

---

## File Structure

```
pre-call-assistant/
├── main.py                          # FastAPI backend — brief, transcribe, speak endpoints
├── requirements.txt                 # Python dependencies
├── .env.example                     # API key template
├── static/
│   └── index.html                   # Frontend — mic button, transcript, brief display, audio player
└── data/
    ├── clienta-account-brief.txt    # Synthetic account brief (upload to Google Drive)
    ├── clienta-meeting-notes.txt    # Synthetic discovery call notes (upload to Google Drive)
    └── clienta-email-summary.txt    # Synthetic email thread summary (upload to Google Drive)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/gtm-ai-notebooks.git
cd gtm-ai-notebooks/article-9-mcp/pre-call-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
ANTHROPIC_API_KEY="your-anthropic-api-key"
ELEVENLABS_API_KEY="your-elevenlabs-api-key"
ELEVENLABS_VOICE_ID="your-elevenlabs-voice-id"
```

- **Anthropic API key:** [console.anthropic.com](https://console.anthropic.com)
- **ElevenLabs API key and Voice ID:** [elevenlabs.io](https://elevenlabs.io) — find both in your profile settings

### 4. Connect MCP servers in Claude Code (VS Code)

This build uses two MCP servers connected through Claude Code in VS Code. You need both configured before running.

Open your Claude Code MCP settings and add:

```json
{
  "mcpServers": {
    "google-drive": {
      "url": "https://drivemcp.googleapis.com/mcp/v1"
    },
    "gmail": {
      "url": "https://gmailmcp.googleapis.com/mcp/v1"
    }
  }
}
```

Authenticate each server when prompted. Both require Google OAuth.

### 5. Upload synthetic data to Google Drive

The `data/` folder contains three pre-built files for the demo. Upload all three to a folder in your Google Drive called **Pre-Call Assistant**:

- `clienta-account-brief.txt` — deal summary, stakeholders, open questions
- `clienta-meeting-notes.txt` — discovery call notes and unresolved action items
- `clienta-email-summary.txt` — email thread history with flagged gaps

The Drive MCP will retrieve these when the agent searches for ClientA context.

### 6. Run the app

```bash
uvicorn main:app --reload
```

Open your browser at [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)

---

## Using the Assistant

1. Click the mic button
2. Ask a question — for example: *"Prep me for my 2pm call with ClientA"*
3. Click the mic button again to stop recording
4. The assistant transcribes your question, pulls context from Drive and Gmail via MCP, generates a structured brief, and reads it back to you

---

## How the MCP Connection Works

The backend calls Claude with two MCP servers attached:

```python
response = anthropic_client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    mcp_servers=[
        {
            "type": "url",
            "url": "https://drivemcp.googleapis.com/mcp/v1",
            "name": "google-drive",
        },
        {
            "type": "url",
            "url": "https://gmailmcp.googleapis.com/mcp/v1",
            "name": "gmail",
        },
    ],
    system=SYSTEM_PROMPT,
    messages=[{"role": "user", "content": query}],
    betas=["mcp-client-2025-04-04"],
)
```

Claude decides which MCP tools to call based on the query. No custom integration code. No brittle connectors. The agent reaches into Gmail and Drive the same way it would reason about anything else.

We use `claude-sonnet-4-6` rather than Opus. For a retrieval and synthesis task like this one, Sonnet gives you the right balance of speed, cost, and output quality. Save Opus for workflows where reasoning complexity genuinely demands it.

---

## Extending This Build

A few directions worth exploring once the base build is working:

- **Add Salesforce MCP** to pull live opportunity data alongside email and Drive context
- **Add a Slack MCP** to surface side conversations between the AE and solutions engineer
- **Swap the query** from account-based to person-based: *"What do I know about Jordan Mills at ClientA?"*
- **Build a post-call version** that logs call summaries back to Drive and drafts follow-up emails via Gmail MCP

---

## About the Series

**Building with Agentic AI** is a practical, builder-focused series for sales, GTM, and marketing practitioners. Each article combines conceptual frameworks with hands-on implementations.

| Article | Topic |
|---|---|
This project is part of Building with Agentic AI, a 10-article series on building production-grade agentic systems for GTM and sales teams.

Article 1: How to Pick the Right Problems for AI Agents and Automation
Article 2: Building AI Agents in Practice: A Sales Outreach Agent with n8n and Claude
Article 3: Bad Prompt, Good Prompt, Great Prompt: The Practical Guide to Prompt Engineering [+ Sales Agent Example]
Article 4: The AI Meeting Prep Assistant: From Problem to a Full Product with n8n and v0
Article 5: RAG for Revenue Teams: From Simple Retrieval to Agentic and Graph RAG
Article 6: Evals for Agentic AI: How to Know If Your System Actually Works + Hands on n8n JSON Files
Article 7: Multi-Agent Systems (this project)
Article 8: Fine-Tuning and Intentional Knowledge Ingestion (coming next)

Follow the series on [Medium](https://sarasoleymani.medium.com/) and [LinkedIn](https://www.linkedin.com/in/sarasoleymani/).

---

## License

MIT
