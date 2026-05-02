import os
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv
import io

load_dotenv()

app = FastAPI(title="Pre-Call Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

SYSTEM_PROMPT = """You are a pre-call intelligence assistant for enterprise sales reps.

When given a query about an upcoming call or account, you must:
1. Search Google Drive for any account briefs, meeting notes, or deal documents related to the account mentioned
2. Search Gmail for recent email threads with contacts from that account
3. Synthesize everything into a structured pre-call brief

Always return your brief in this exact format:

DEAL STATUS
- Stage, deal value, expected close date, and competing vendor if known

RECENT EMAIL CONTEXT
- Summary of the last 2-3 email exchanges, flagging any unanswered commitments

OPEN QUESTIONS
- Unresolved questions or action items that need to be addressed on this call

FLAGGED RISKS
- Stakeholder gaps, outstanding deliverables, or deal risks that need immediate attention

Be direct and specific. A sales rep is reading this 10 minutes before a call. Every word should be useful."""


class BriefRequest(BaseModel):
    query: str


@app.post("/brief")
async def generate_brief(request: BriefRequest):
    """Generate a pre-call brief using Claude with MCP connections to Gmail and Google Drive."""
    try:
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
            messages=[{"role": "user", "content": request.query}],
            betas=["mcp-client-2025-04-04"],
        )

        brief_text = ""
        for block in response.content:
            if block.type == "text":
                brief_text += block.text

        return JSONResponse(content={"summary": brief_text})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using ElevenLabs speech-to-text."""
    try:
        audio_bytes = await audio.read()

        response = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            files={"audio": (audio.filename, audio_bytes, audio.content_type)},
            data={"model_id": "scribe_v1"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ElevenLabs transcription error: {response.text}",
            )

        result = response.json()
        return JSONResponse(content={"text": result.get("text", "")})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speak")
async def text_to_speech(request: BriefRequest):
    """Convert text to speech using ElevenLabs."""
    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": request.query,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ElevenLabs TTS error: {response.text}",
            )

        return StreamingResponse(
            io.BytesIO(response.content),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=brief.mp3"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Pre-Call Assistant API is running"}
