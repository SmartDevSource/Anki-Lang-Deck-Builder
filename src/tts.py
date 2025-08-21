import hashlib, os, asyncio
import edge_tts

async def generate_mp3(text, voice, output_dir):
    hsh = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    fname = f"{hsh}.mp3"
    out_path = os.path.join(output_dir, fname)
    await edge_tts.Communicate(text, voice=voice).save(out_path)
    return fname
