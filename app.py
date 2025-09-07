from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import io, re, time, hashlib, httpx, os, tempfile, base64
import genanki

app = FastAPI(title="apkg-maker")

def safe_name(s: str, fallback: str = "") -> str:
    s = (s or "").strip()
    s = re.sub(r"[^A-Za-z0-9_\-\.]+", "_", s)
    return s or (fallback or f"card_{int(time.time())}")

class NoteIn(BaseModel):
    front: str = Field(..., description="Front side")
    backHtml: str = Field(..., description="HTML back")
    audioUrl: Optional[str] = None
    audioBase64: Optional[str] = None

class MakeApkgIn(BaseModel):
    deckName: str = Field("English::Telegram")
    notes: List[NoteIn] = Field(..., min_items=1)

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/apkg")
async def make_apkg(data: MakeApkgIn):
    try:
        deck_id = int(hashlib.sha1(data.deckName.encode()).hexdigest()[:8], 16)
        model_id = int(hashlib.sha1(b"Basic_HTML_model").hexdigest()[:8], 16)

        model = genanki.Model(
            model_id,
            "Basic (HTML)",
            fields=[{"name": "Front"}, {"name": "Back"}],
            templates=[{
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{FrontSide}}<hr id=\"answer\">{{Back}}",
            }],
            css=".card{font-family:arial;font-size:16px;color:#222;text-align:left}hr{margin:12px 0}",
        )
        deck = genanki.Deck(deck_id, data.deckName)

        media_tmpdir = tempfile.TemporaryDirectory()
        media_paths: List[str] = []

        async with httpx.AsyncClient(timeout=15.0) as client:
            for n in data.notes:
                front = (n.front or "").strip()
                back = (n.backHtml or "").strip()
                if not front or not back:
                    raise HTTPException(status_code=400, detail="front and backHtml are required")

                # audio: сначала base64, потом URL
                content_bytes = None
                if n.audioBase64:
                    try:
                        content_bytes = base64.b64decode(n.audioBase64)
                    except Exception:
                        content_bytes = None

                if not content_bytes and n.audioUrl:
                    try:
                        r = await client.get(n.audioUrl)
                        r.raise_for_status()
                        content_bytes = r.content
                    except Exception:
                        content_bytes = None

                if content_bytes:
                    fname = f"{safe_name(front)}.mp3"
                    p = os.path.join(media_tmpdir.name, fname)
                    with open(p, "wb") as f:
                        f.write(content_bytes)
                    media_paths.append(p)
                    # Если нужен плеер на обороте, раскомментируй:
                    # back += f'<div style="margin-top:8px;"><audio controls src="{fname}"></audio></div>'

                note_obj = genanki.Note(
                    model=model,
                    fields=[front, back],
                    guid=hashlib.sha1(front.encode()).hexdigest(),
                )
                deck.add_note(note_obj)

        # genanki пишет только в файл — используем временный файл
        with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as tf:
            out_path = tf.name

        pkg = genanki.Package(deck)
        if media_paths:
            pkg.media_files = media_paths
        pkg.write_to_file(out_path)

        with open(out_path, "rb") as f:
            apkg_bytes = f.read()

        os.unlink(out_path)
        media_tmpdir.cleanup()

        if len(data.notes) == 1:
            file_name = f"{safe_name(data.notes[0].front, 'card')}.apkg"
        else:
            file_name = f"{safe_name(data.deckName, 'deck')}_{int(time.time())}.apkg"

        return StreamingResponse(
            io.BytesIO(apkg_bytes),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename=\"{file_name}\"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

