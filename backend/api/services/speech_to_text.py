"""
Speech-to-Text Service

Converts audio files to text using Google Cloud Speech-to-Text API.
Supports speaker diarization (identifying who said what).
"""

import os
from typing import Optional
from dataclasses import dataclass
from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import cloud_speech

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "")
REGION = os.getenv("REGION", "asia-northeast1")  # or "us-central1" for Chirp
USE_LOCAL_MODE = os.getenv("USE_LOCAL_DB", "false").lower() == "true"

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = {
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.flac': 'audio/flac',
    '.ogg': 'audio/ogg',
    '.m4a': 'audio/mp4',
    '.webm': 'audio/webm',
    '.opus': 'audio/opus',
}


@dataclass
class TranscriptionSegment:
    """A segment of transcribed speech with speaker info."""
    speaker: Optional[str]
    text: str
    start_time: float  # seconds
    end_time: float  # seconds
    confidence: float


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    segments: list[TranscriptionSegment]
    full_text: str
    speakers: list[str]
    duration_seconds: float
    language: str


def is_audio_file(filename: str) -> bool:
    """Check if the file is a supported audio format."""
    ext = os.path.splitext(filename.lower())[1]
    return ext in SUPPORTED_AUDIO_FORMATS


def get_audio_mime_type(filename: str) -> Optional[str]:
    """Get the MIME type for an audio file."""
    ext = os.path.splitext(filename.lower())[1]
    return SUPPORTED_AUDIO_FORMATS.get(ext)


def transcribe_audio(
    audio_content: bytes,
    filename: str,
    language_code: str = "ja-JP",
    enable_diarization: bool = True,
    min_speakers: int = 2,
    max_speakers: int = 6,
    model: str = "long"  # "long" for meetings, "chirp" for highest accuracy
) -> TranscriptionResult:
    """
    Transcribe audio file to text with speaker diarization.
    
    Args:
        audio_content: Raw audio file bytes
        filename: Original filename (for format detection)
        language_code: BCP-47 language code (default: ja-JP for Japanese)
        enable_diarization: Enable speaker diarization (who said what)
        min_speakers: Minimum expected speakers
        max_speakers: Maximum expected speakers
        model: Recognition model - "long" for long-form, "chirp" for highest accuracy
    
    Returns:
        TranscriptionResult with segments, full text, and speaker info
    """
    
    if USE_LOCAL_MODE:
        # In local mode, return mock data or use alternative
        return _mock_transcription(audio_content, filename)
    
    # Initialize Speech-to-Text client
    client = speech.SpeechClient()
    
    # Determine recognizer path
    # For Chirp model, use us-central1 region
    recognizer_region = "us-central1" if model == "chirp" else REGION
    recognizer_name = f"projects/{PROJECT_ID}/locations/{recognizer_region}/recognizers/_"
    
    # Configure recognition
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[language_code],
        model=model,
        features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            enable_word_confidence=True,
            diarization_config=cloud_speech.SpeakerDiarizationConfig(
                min_speaker_count=min_speakers,
                max_speaker_count=max_speakers,
            ) if enable_diarization else None,
        ),
    )
    
    # Create request
    request = cloud_speech.RecognizeRequest(
        recognizer=recognizer_name,
        config=config,
        content=audio_content,
    )
    
    # Perform transcription
    response = client.recognize(request=request)
    
    # Process results
    return _process_response(response, language_code)


def transcribe_audio_gcs(
    gcs_uri: str,
    language_code: str = "ja-JP",
    enable_diarization: bool = True,
    min_speakers: int = 2,
    max_speakers: int = 6,
    model: str = "long"
) -> TranscriptionResult:
    """
    Transcribe audio file from Google Cloud Storage.
    Use this for files larger than 10MB.
    
    Args:
        gcs_uri: GCS URI of the audio file (gs://bucket/path/file.mp3)
        language_code: BCP-47 language code
        enable_diarization: Enable speaker diarization
        min_speakers: Minimum expected speakers
        max_speakers: Maximum expected speakers
        model: Recognition model
    
    Returns:
        TranscriptionResult
    """
    
    if USE_LOCAL_MODE:
        return _mock_transcription(b"", "audio.mp3")
    
    client = speech.SpeechClient()
    
    recognizer_region = "us-central1" if model == "chirp" else REGION
    recognizer_name = f"projects/{PROJECT_ID}/locations/{recognizer_region}/recognizers/_"
    
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[language_code],
        model=model,
        features=cloud_speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
            enable_word_confidence=True,
            diarization_config=cloud_speech.SpeakerDiarizationConfig(
                min_speaker_count=min_speakers,
                max_speaker_count=max_speakers,
            ) if enable_diarization else None,
        ),
    )
    
    # For long audio files, use batch recognize
    file_metadata = cloud_speech.BatchRecognizeFileMetadata(uri=gcs_uri)
    
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=recognizer_name,
        config=config,
        files=[file_metadata],
        recognition_output_config=cloud_speech.RecognitionOutputConfig(
            inline_response_config=cloud_speech.InlineOutputConfig(),
        ),
    )
    
    # Long running operation
    operation = client.batch_recognize(request=request)
    response = operation.result(timeout=600)  # 10 minutes timeout
    
    # Process batch results
    for file_result in response.results.values():
        if file_result.transcript:
            return _process_batch_response(file_result.transcript, language_code)
    
    # Empty result
    return TranscriptionResult(
        segments=[],
        full_text="",
        speakers=[],
        duration_seconds=0,
        language=language_code
    )


def _process_response(
    response: cloud_speech.RecognizeResponse,
    language_code: str
) -> TranscriptionResult:
    """Process synchronous recognition response."""
    segments = []
    full_text_parts = []
    speakers_set = set()
    max_end_time = 0.0
    
    for result in response.results:
        if not result.alternatives:
            continue
        
        alternative = result.alternatives[0]
        
        # Process words with speaker info
        current_speaker = None
        current_words = []
        segment_start = 0.0
        
        for word_info in alternative.words:
            speaker_tag = getattr(word_info, 'speaker_tag', 0)
            speaker_label = f"Speaker {speaker_tag}" if speaker_tag > 0 else None
            
            if speaker_label:
                speakers_set.add(speaker_label)
            
            word_start = word_info.start_offset.total_seconds() if word_info.start_offset else 0
            word_end = word_info.end_offset.total_seconds() if word_info.end_offset else 0
            max_end_time = max(max_end_time, word_end)
            
            # If speaker changed, save current segment
            if speaker_label != current_speaker and current_words:
                segments.append(TranscriptionSegment(
                    speaker=current_speaker,
                    text=' '.join(current_words),
                    start_time=segment_start,
                    end_time=word_start,
                    confidence=alternative.confidence if hasattr(alternative, 'confidence') else 0.0
                ))
                current_words = []
                segment_start = word_start
            
            current_speaker = speaker_label
            current_words.append(word_info.word)
        
        # Save last segment
        if current_words:
            segments.append(TranscriptionSegment(
                speaker=current_speaker,
                text=' '.join(current_words),
                start_time=segment_start,
                end_time=max_end_time,
                confidence=alternative.confidence if hasattr(alternative, 'confidence') else 0.0
            ))
        
        full_text_parts.append(alternative.transcript)
    
    # Generate full text with speaker labels
    full_text = _segments_to_text(segments)
    
    return TranscriptionResult(
        segments=segments,
        full_text=full_text,
        speakers=sorted(list(speakers_set)),
        duration_seconds=max_end_time,
        language=language_code
    )


def _process_batch_response(
    transcript: cloud_speech.Transcript,
    language_code: str
) -> TranscriptionResult:
    """Process batch recognition response."""
    segments = []
    speakers_set = set()
    max_end_time = 0.0
    
    for result in transcript.results:
        if not result.alternatives:
            continue
        
        alternative = result.alternatives[0]
        
        current_speaker = None
        current_words = []
        segment_start = 0.0
        
        for word_info in alternative.words:
            speaker_tag = getattr(word_info, 'speaker_label', '') or getattr(word_info, 'speaker_tag', 0)
            if isinstance(speaker_tag, int) and speaker_tag > 0:
                speaker_label = f"Speaker {speaker_tag}"
            elif isinstance(speaker_tag, str) and speaker_tag:
                speaker_label = speaker_tag
            else:
                speaker_label = None
            
            if speaker_label:
                speakers_set.add(speaker_label)
            
            word_start = word_info.start_offset.total_seconds() if word_info.start_offset else 0
            word_end = word_info.end_offset.total_seconds() if word_info.end_offset else 0
            max_end_time = max(max_end_time, word_end)
            
            if speaker_label != current_speaker and current_words:
                segments.append(TranscriptionSegment(
                    speaker=current_speaker,
                    text=' '.join(current_words),
                    start_time=segment_start,
                    end_time=word_start,
                    confidence=alternative.confidence if hasattr(alternative, 'confidence') else 0.0
                ))
                current_words = []
                segment_start = word_start
            
            current_speaker = speaker_label
            current_words.append(word_info.word)
        
        if current_words:
            segments.append(TranscriptionSegment(
                speaker=current_speaker,
                text=' '.join(current_words),
                start_time=segment_start,
                end_time=max_end_time,
                confidence=alternative.confidence if hasattr(alternative, 'confidence') else 0.0
            ))
    
    full_text = _segments_to_text(segments)
    
    return TranscriptionResult(
        segments=segments,
        full_text=full_text,
        speakers=sorted(list(speakers_set)),
        duration_seconds=max_end_time,
        language=language_code
    )


def _segments_to_text(segments: list[TranscriptionSegment]) -> str:
    """Convert segments to formatted text with speaker labels."""
    lines = []
    for segment in segments:
        if segment.speaker:
            lines.append(f"{segment.speaker}: {segment.text}")
        else:
            lines.append(segment.text)
    return '\n\n'.join(lines)


def _mock_transcription(audio_content: bytes, filename: str) -> TranscriptionResult:
    """Return mock transcription for local development."""
    mock_segments = [
        TranscriptionSegment(
            speaker="Speaker 1",
            text="本日はプロジェクトの進捗確認を行います。",
            start_time=0.0,
            end_time=5.0,
            confidence=0.95
        ),
        TranscriptionSegment(
            speaker="Speaker 2",
            text="はい、現在の状況を報告します。開発は順調に進んでいます。",
            start_time=5.0,
            end_time=12.0,
            confidence=0.92
        ),
        TranscriptionSegment(
            speaker="Speaker 1",
            text="リスクについて何かありますか？",
            start_time=12.0,
            end_time=15.0,
            confidence=0.94
        ),
        TranscriptionSegment(
            speaker="Speaker 2",
            text="スケジュールが厳しいかもしれません。来週のリリースに間に合うか心配しています。",
            start_time=15.0,
            end_time=22.0,
            confidence=0.91
        ),
    ]
    
    return TranscriptionResult(
        segments=mock_segments,
        full_text=_segments_to_text(mock_segments),
        speakers=["Speaker 1", "Speaker 2"],
        duration_seconds=22.0,
        language="ja-JP"
    )


def get_supported_audio_formats() -> list[dict]:
    """Return list of supported audio formats."""
    return [
        {"extension": ext, "mime_type": mime, "description": _get_format_description(ext)}
        for ext, mime in SUPPORTED_AUDIO_FORMATS.items()
    ]


def _get_format_description(ext: str) -> str:
    """Get human-readable description for audio format."""
    descriptions = {
        '.mp3': 'MP3音声ファイル',
        '.wav': 'WAV音声ファイル（高品質）',
        '.flac': 'FLAC音声ファイル（ロスレス）',
        '.ogg': 'OGG音声ファイル',
        '.m4a': 'M4A/AAC音声ファイル（iPhone録音等）',
        '.webm': 'WebM音声ファイル（ブラウザ録音）',
        '.opus': 'Opus音声ファイル',
    }
    return descriptions.get(ext, '音声ファイル')

