# -*- coding: utf-8 -*-
"""
FFmpeg API Service for n8n Video Automation.

This FastAPI application provides a highly optimized, single endpoint 
to perform all FFmpeg/FFprobe operations for video creation.

Version: 6.2.1 (Final - Including all helper functions)
"""
# --- Core Imports ---
import asyncio
import json
import os
import shutil
import shlex
import uuid
from typing import Dict

# --- Library Imports ---
import aiohttp
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

# ==============================================================================
# 1. APPLICATION CONFIGURATION & SETUP
# ==============================================================================
app = FastAPI(
    title="FFmpeg as a Service for n8n",
    description="A robust API to create full videos with crossfade transitions.",
    version="6.2.1",
)

TEMP_DIR = "/tmp/ffmpeg_processing"
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ==============================================================================
# 2. LIFECYCLE & HELPER FUNCTIONS
# ==============================================================================
@app.on_event("startup")
async def startup_event():
    """Ensure the temporary processing directory exists on startup."""
    os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_directory(directory_path: str):
    """
    Safely removes a directory and its contents after processing.
    """
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path, ignore_errors=True)
        print(f"--- CLEANUP: Successfully removed {directory_path} ---")

async def run_subprocess(command: str) -> (str, str):
    """
    Executes a shell command asynchronously, capturing its output.
    Raises RuntimeError on failure.
    """
    print(f"--- EXECUTING COMMAND ---\n{command}\n-------------------------")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_message = stderr.decode(errors='ignore').strip()
        print(f"ERROR: Command failed.\nStderr: {error_message}")
        raise RuntimeError(f"FFmpeg command failed: {error_message}")
    
    print("SUCCESS: Command executed.")
    return stdout.decode(errors='ignore'), stderr.decode(errors='ignore')

# >>>>> FUNÇÃO AUXILIAR QUE ESTAVA FALTANDO <<<<<
async def download_asset(session: aiohttp.ClientSession, url: str, path: str, asset_type: str = "image"):
    """
    Downloads a single asset from a URL to a local path.
    """
    print(f"Downloading {asset_type} from {url}...")
    async with session.get(url) as resp:
        if not resp.ok:
            raise IOError(f"Failed to download {asset_type} from {url}, status: {resp.status}")
        with open(path, "wb") as f:
            f.write(await resp.read())

# ==============================================================================
# 3. ENDPOINT "TUDO-EM-UM" OTIMIZADO (VERSÃO FINAL)
# ==============================================================================

@app.post("/create-full-video-with-subtitles/")
async def create_full_video_final(
    image_urls_json: str = Form(...),
    audio_url: str = Form(...),
    subtitle_file: UploadFile = File(...),
    output_filename: str = Form("final_video.mp4")
):
    unique_id = str(uuid.uuid4())
    temp_processing_dir = os.path.join(TEMP_DIR, unique_id)
    os.makedirs(temp_processing_dir)
    
    audio_path = os.path.join(temp_processing_dir, "narracao.mp3")
    subtitle_path = os.path.join(temp_processing_dir, "subtitle.ass")
    
    try:
        # ETAPA 1: Aquisição de todos os ativos
        print("--- STEP 1/6: ACQUIRING ASSETS ---")
        with open(subtitle_path, "wb") as buffer:
            shutil.copyfileobj(subtitle_file.file, buffer)
        
        image_urls = json.loads(image_urls_json)
        local_image_paths = []
        
        async with aiohttp.ClientSession(headers=BROWSER_HEADERS) as session:
            await download_asset(session, audio_url, audio_path, "audio")
            for i, url in enumerate(image_urls):
                local_path = os.path.join(temp_processing_dir, f"image_{i:02d}.jpg")
                await download_asset(session, url, local_path, f"image {i+1}")
                local_image_paths.append(local_path)
        print("SUCCESS: All assets acquired.")

        # ETAPA 2: Obter Duração precisa do Áudio
        print("--- STEP 2/6: GETTING AUDIO DURATION ---")
        cmd_ffprobe = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {shlex.quote(audio_path)}"
        stdout, _ = await run_subprocess(cmd_ffprobe)
        total_duration = float(stdout.strip())
        print(f"SUCCESS: Audio duration is {total_duration} seconds.")

        # ETAPA 3: Criar Vídeo com Transições - LÓGICA DE TEMPO CORRIGIDA
        print("--- STEP 3/6: CREATING VIDEO WITH PRECISE CROSSFADE TRANSITIONS ---")
        
        transition_duration = 1.0
        num_images = len(local_image_paths)
        
        if num_images <= 1:
            raise ValueError("At least two images are required for transitions.")

        # Esta é a matemática correta para calcular a duração estática de cada cena.
        display_duration = (total_duration - transition_duration) / (num_images - 1)

        if display_duration <= 0:
            raise ValueError("Audio is too short for the number of images and transition duration.")

        input_args = ""
        # Cada clipe de imagem precisa durar o tempo de display + o tempo da transição
        clip_duration = display_duration + transition_duration
        for path in local_image_paths:
            input_args += f"-loop 1 -t {clip_duration} -i {shlex.quote(path)} "

        filter_complex_chain = ""
        last_stream = "0:v"
        
        for i in range(num_images - 1):
            next_stream_idx = i + 1
            output_stream_name = f"v{next_stream_idx}"
            
            # O offset para cada transição é o tempo estático da cena.
            offset = display_duration
            
            # Na cadeia, o offset é relativo ao início do clipe combinado, não ao tempo absoluto.
            # O `xfade` precisa de um offset que se refere ao tempo do stream de saída.
            # A lógica cumulativa é a mais correta.
            cumulative_offset = (i + 1) * display_duration
            
            filter_part = f"[{last_stream}][{next_stream_idx}:v]xfade=transition=fade:duration={transition_duration}:offset={cumulative_offset}[{output_stream_name}];"
            filter_complex_chain += filter_part
            last_stream = output_stream_name

        silent_video_path = os.path.join(temp_processing_dir, "silent_video_with_transitions.mp4")
        
        final_filter_chain = f"{filter_complex_chain}[{last_stream}]format=yuv420p,fps=25[final_v]"

        cmd_video_transitions = (
            f"ffmpeg {input_args} "
            f"-filter_complex \"{final_filter_chain}\" "
            f"-map \"[final_v]\" -an -y {shlex.quote(silent_video_path)}"
        )
        
        await run_subprocess(cmd_video_transitions)
        print("SUCCESS: Video with transitions created.")
        
        # ETAPA 4: Combinar com áudio
        print("--- STEP 4/6: COMBINING WITH AUDIO ---")
        video_with_audio_path = os.path.join(temp_processing_dir, "video_with_audio.mp4")
        cmd_combine = (f"ffmpeg -i {shlex.quote(silent_video_path)} -i {shlex.quote(audio_path)} "
                       f"-c:v copy -c:a aac -shortest -y {shlex.quote(video_with_audio_path)}")
        await run_subprocess(cmd_combine)

        # ETAPA 5: Adicionar Legendas
        print("--- STEP 5/6: BURNING SUBTITLES ---")
        final_output_path = os.path.join(temp_processing_dir, output_filename)
        escaped_subtitle_path = subtitle_path.replace("'", "'\\''")
        
        cmd_subtitles = (
            f"ffmpeg -i {shlex.quote(video_with_audio_path)} "
            f"-vf \"ass='{escaped_subtitle_path}'\" "
            f"-c:v libx264 -preset ultrafast -c:a copy "
            f"-y {shlex.quote(final_output_path)}"
        )
        await run_subprocess(cmd_subtitles)
        print("--- STEP 6/6: FINAL VIDEO CREATED SUCCESSFULLY ---")

        cleanup_task = BackgroundTask(cleanup_directory, directory_path=temp_processing_dir)
        return FileResponse(
            path=final_output_path,
            filename=output_filename,
            media_type="video/mp4",
            background=cleanup_task
        )

    except Exception as e:
        cleanup_directory(directory_path=temp_processing_dir)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")