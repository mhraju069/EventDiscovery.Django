import os, uuid, subprocess
from django.core.files import File
from rest_framework.response import Response
from .models import ChatRoom, Message


def get_chat_name(user1,user2):
    name1 = user1.email.split('@')[0]
    name2 = user2.email.split('@')[0]
    return f"{name1} and {name2}"


def reduce_noise(message, name):
    pcm_in = None
    pcm_out = None
    clean_wav = None
    try:
        audio = message.file
        if not audio:
            return message

        uid = uuid.uuid4().hex
        pcm_in = f"/tmp/{uid}_in.pcm"
        pcm_out = f"/tmp/{uid}_out.pcm"
        clean_wav = f"/tmp/{uid}_clean.wav"
        
        # Ensure we have a valid path for input
        input_path = audio.path
        
        # RNNoise requires 48kHz sampling rate for correct operation
        sample_rate = "48000" 

        # WAV → PCM
        subprocess.run([
            "ffmpeg", "-y",
            "-i", input_path,
            "-ac", "1",
            "-ar", sample_rate,
            "-f", "s16le",
            pcm_in
        ], check=True)

        # RNNoise
        subprocess.run([
            "rnnoise_demo",
            pcm_in,
            pcm_out
        ], check=True)

        # PCM → WAV
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "s16le",
            "-ar", sample_rate,
            "-ac", "1",
            "-i", pcm_out,
            clean_wav
        ], check=True)

        # Save cleaned audio
        with open(clean_wav, "rb") as f:
            new_filename = f"clean_{name}" if not name.startswith("clean_") else name
            message.file.save(new_filename, File(f))
            
            if input_path and os.path.exists(input_path):
                if os.path.abspath(input_path) != os.path.abspath(message.file.path):
                     try:
                        os.remove(input_path)
                     except Exception as e:
                        print(f"Error deleting original file: {e}")

        message.save()

        return message

    except Exception as e:
        print(f"Error in reduce_noise: {str(e)}")
        return message
    
    finally:
        # Cleanup temporary files
        for fpath in [pcm_in, pcm_out, clean_wav]:
            if fpath and os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass


def add_seen_by(room_id, user):
    room = ChatRoom.objects.filter(id=room_id).first()
    if not room:
        return False
    
    messages = Message.objects.filter(room=room).exclude(sender=user).exclude(seen_by=user)
    
    for msg in messages:
        msg.seen_by.add(user)
    
    return True