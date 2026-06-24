import os
import logging
import av

logger = logging.getLogger("PrivaSub.AudioExtractor")

def extract_audio_to_wav(input_path: str, output_path: str, progress_callback=None) -> bool:
    """
    Extracts audio from any video or audio file and resamples it to 16kHz mono WAV.
    Runs 100% locally and offline using PyAV (FFmpeg bindings).
    
    :param input_path: Path to the input video or audio file.
    :param output_path: Path to write the output 16kHz mono WAV file.
    :param progress_callback: Optional function(progress_percent: float) to report progress.
    :return: True if successful, False otherwise.
    """
    logger.info(f"Starting audio extraction: {input_path} -> {output_path}")
    input_container = None
    output_container = None
    try:
        # Open the input file
        input_container = av.open(input_path)
        
        # Find the first audio stream
        audio_stream = next((s for s in input_container.streams if s.type == 'audio'), None)
        if not audio_stream:
            raise ValueError("No audio stream found in the input file.")
            
        # Get total duration of the file in seconds
        total_duration = float(input_container.duration) / 1000000.0 if input_container.duration else None
        logger.info(f"Audio stream found. Codec: {audio_stream.name}, Duration: {total_duration}s")

        # Open the output WAV container
        output_container = av.open(output_path, mode='w', format='wav')
        
        # Add uncompressed pcm_s16le stream
        output_stream = output_container.add_stream('pcm_s16le', rate=16000)
        output_stream.layout = 'mono'
        output_stream.format = 's16'  # signed 16-bit PCM

        # Initialize the resampler to target 16kHz mono s16 PCM
        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)

        # Decode frames and process
        for packet in input_container.demux(audio_stream):
            for frame in packet.decode():
                # Resample frame
                resampled_frames = resampler.resample(frame)
                if resampled_frames:
                    for resampled_frame in resampled_frames:
                        # Encode and write
                        packets = output_stream.encode(resampled_frame)
                        for p in packets:
                            output_container.mux(p)
                            
                # Report progress
                if progress_callback and total_duration and frame.time:
                    progress_percent = min(99.0, (float(frame.time) / total_duration) * 100.0)
                    progress_callback(progress_percent)

        # Flush resampler
        resampled_frames = resampler.resample(None)
        if resampled_frames:
            for resampled_frame in resampled_frames:
                packets = output_stream.encode(resampled_frame)
                for p in packets:
                    output_container.mux(p)

        # Flush encoder
        packets = output_stream.encode(None)
        for p in packets:
            output_container.mux(p)

        if progress_callback:
            progress_callback(100.0)
            
        logger.info("Audio extraction completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        return False
        
    finally:
        if input_container:
            input_container.close()
        if output_container:
            output_container.close()
