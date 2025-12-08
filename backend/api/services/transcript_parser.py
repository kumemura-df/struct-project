"""
Transcript Parser Service

Parses various transcript file formats from different sources:
- VTT (WebVTT) - Zoom, YouTube, Google Meet
- SRT (SubRip) - Common subtitle format
- Otter.ai export format
- tl;dv export format
- Plain text with timestamps
"""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class TranscriptFormat(Enum):
    """Supported transcript formats"""
    VTT = "vtt"
    SRT = "srt"
    OTTER = "otter"
    TLDV = "tldv"
    ZOOM_TXT = "zoom_txt"
    PLAIN = "plain"


@dataclass
class TranscriptSegment:
    """A single segment of the transcript"""
    start_time: Optional[str]
    end_time: Optional[str]
    speaker: Optional[str]
    text: str


@dataclass
class ParsedTranscript:
    """Parsed transcript result"""
    format: TranscriptFormat
    segments: list[TranscriptSegment]
    raw_text: str
    metadata: dict


def detect_format(content: str, filename: str = "") -> TranscriptFormat:
    """
    Detect the format of the transcript file.
    
    Args:
        content: File content as string
        filename: Original filename (optional, helps with detection)
    
    Returns:
        TranscriptFormat enum value
    """
    content_lower = content.lower().strip()
    filename_lower = filename.lower()
    
    # Check by file extension first
    if filename_lower.endswith('.vtt'):
        return TranscriptFormat.VTT
    if filename_lower.endswith('.srt'):
        return TranscriptFormat.SRT
    
    # Check by content signature
    if content_lower.startswith('webvtt'):
        return TranscriptFormat.VTT
    
    # SRT format: starts with number, then timestamp line
    srt_pattern = r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}'
    if re.match(srt_pattern, content.strip()):
        return TranscriptFormat.SRT
    
    # Otter.ai format detection
    # Typically has speaker names followed by timestamps and text
    if 'otter.ai' in content_lower or re.search(r'^[A-Za-z\s]+\s+\d{1,2}:\d{2}$', content, re.MULTILINE):
        return TranscriptFormat.OTTER
    
    # tl;dv format detection
    if 'tl;dv' in content_lower or 'tldv' in content_lower:
        return TranscriptFormat.TLDV
    
    # Zoom TXT format: [HH:MM:SS] Speaker: text
    if re.search(r'\[\d{2}:\d{2}:\d{2}\]\s+\w+:', content):
        return TranscriptFormat.ZOOM_TXT
    
    # Default to plain text
    return TranscriptFormat.PLAIN


def parse_vtt(content: str) -> ParsedTranscript:
    """
    Parse WebVTT format transcript.
    
    Format example:
    WEBVTT
    
    00:00:00.000 --> 00:00:05.000
    Speaker Name: Hello everyone
    
    00:00:05.000 --> 00:00:10.000
    Another Speaker: Hi there
    """
    segments = []
    lines = content.split('\n')
    
    i = 0
    # Skip header
    while i < len(lines) and not re.match(r'\d{2}:\d{2}:\d{2}', lines[i]):
        i += 1
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Match timestamp line
        timestamp_match = re.match(
            r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})',
            line
        )
        
        if timestamp_match:
            start_time = timestamp_match.group(1)
            end_time = timestamp_match.group(2)
            
            # Collect text lines until next timestamp or empty line
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip() and not re.match(r'\d{2}:\d{2}:\d{2}', lines[i]):
                text_lines.append(lines[i].strip())
                i += 1
            
            if text_lines:
                full_text = ' '.join(text_lines)
                
                # Try to extract speaker
                speaker = None
                text = full_text
                speaker_match = re.match(r'^([^:]+):\s*(.+)$', full_text)
                if speaker_match:
                    speaker = speaker_match.group(1).strip()
                    text = speaker_match.group(2).strip()
                
                segments.append(TranscriptSegment(
                    start_time=start_time,
                    end_time=end_time,
                    speaker=speaker,
                    text=text
                ))
        else:
            i += 1
    
    raw_text = _segments_to_text(segments)
    
    return ParsedTranscript(
        format=TranscriptFormat.VTT,
        segments=segments,
        raw_text=raw_text,
        metadata={"segment_count": len(segments)}
    )


def parse_srt(content: str) -> ParsedTranscript:
    """
    Parse SRT (SubRip) format transcript.
    
    Format example:
    1
    00:00:00,000 --> 00:00:05,000
    Hello everyone
    
    2
    00:00:05,000 --> 00:00:10,000
    How are you?
    """
    segments = []
    
    # Split by double newlines (SRT block separator)
    blocks = re.split(r'\n\s*\n', content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        
        # Find timestamp line
        timestamp_line = None
        text_start_idx = 0
        
        for idx, line in enumerate(lines):
            if '-->' in line:
                timestamp_line = line
                text_start_idx = idx + 1
                break
        
        if not timestamp_line:
            continue
        
        # Parse timestamp
        timestamp_match = re.match(
            r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
            timestamp_line
        )
        
        if timestamp_match:
            start_time = timestamp_match.group(1).replace(',', '.')
            end_time = timestamp_match.group(2).replace(',', '.')
            
            # Get text (remaining lines)
            text_lines = lines[text_start_idx:]
            full_text = ' '.join(line.strip() for line in text_lines if line.strip())
            
            # Try to extract speaker
            speaker = None
            text = full_text
            speaker_match = re.match(r'^([^:]+):\s*(.+)$', full_text)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                text = speaker_match.group(2).strip()
            
            segments.append(TranscriptSegment(
                start_time=start_time,
                end_time=end_time,
                speaker=speaker,
                text=text
            ))
    
    raw_text = _segments_to_text(segments)
    
    return ParsedTranscript(
        format=TranscriptFormat.SRT,
        segments=segments,
        raw_text=raw_text,
        metadata={"segment_count": len(segments)}
    )


def parse_otter(content: str) -> ParsedTranscript:
    """
    Parse Otter.ai export format.
    
    Common formats:
    1. Speaker Name  0:00
       Text content here
       
    2. [0:00] Speaker Name
       Text content
       
    3. Speaker Name (0:00)
       Text content
    """
    segments = []
    lines = content.split('\n')
    
    current_speaker = None
    current_time = None
    current_text_lines = []
    
    # Pattern for "Speaker Name  0:00" or "Speaker Name  00:00:00"
    pattern1 = re.compile(r'^([A-Za-z\u3040-\u9fff\s]+)\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*$')
    # Pattern for "[0:00] Speaker Name" 
    pattern2 = re.compile(r'^\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+?):\s*$')
    # Pattern for "Speaker Name (0:00)"
    pattern3 = re.compile(r'^([A-Za-z\u3040-\u9fff\s]+)\s*\((\d{1,2}:\d{2}(?::\d{2})?)\)\s*$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to match header patterns
        match1 = pattern1.match(line)
        match2 = pattern2.match(line)
        match3 = pattern3.match(line)
        
        if match1 or match2 or match3:
            # Save previous segment
            if current_text_lines:
                segments.append(TranscriptSegment(
                    start_time=current_time,
                    end_time=None,
                    speaker=current_speaker,
                    text=' '.join(current_text_lines)
                ))
                current_text_lines = []
            
            # Start new segment
            if match1:
                current_speaker = match1.group(1).strip()
                current_time = match1.group(2)
            elif match2:
                current_time = match2.group(1)
                current_speaker = match2.group(2).strip()
            else:
                current_speaker = match3.group(1).strip()
                current_time = match3.group(2)
        else:
            # Content line
            current_text_lines.append(line)
    
    # Save last segment
    if current_text_lines:
        segments.append(TranscriptSegment(
            start_time=current_time,
            end_time=None,
            speaker=current_speaker,
            text=' '.join(current_text_lines)
        ))
    
    # If no segments detected, treat as plain text
    if not segments:
        return parse_plain(content)
    
    raw_text = _segments_to_text(segments)
    
    return ParsedTranscript(
        format=TranscriptFormat.OTTER,
        segments=segments,
        raw_text=raw_text,
        metadata={"segment_count": len(segments), "speakers": list(set(s.speaker for s in segments if s.speaker))}
    )


def parse_tldv(content: str) -> ParsedTranscript:
    """
    Parse tl;dv export format.
    
    tl;dv typically exports in markdown-like format:
    
    ## Meeting Title
    **Date:** 2024-12-08
    
    ### Transcript
    
    **Speaker Name** (00:00:00)
    Text content here
    
    **Another Speaker** (00:01:30)
    More text here
    """
    segments = []
    lines = content.split('\n')
    
    current_speaker = None
    current_time = None
    current_text_lines = []
    
    # Pattern for "**Speaker Name** (00:00:00)" or "Speaker Name (00:00:00)"
    speaker_pattern = re.compile(r'^\*{0,2}([^*\(]+?)\*{0,2}\s*\((\d{1,2}:\d{2}(?::\d{2})?)\)\s*$')
    
    in_transcript = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip until we find transcript section
        if '### transcript' in line_stripped.lower() or '## transcript' in line_stripped.lower():
            in_transcript = True
            continue
        
        if not line_stripped:
            continue
        
        # Skip metadata lines
        if line_stripped.startswith('#') or line_stripped.startswith('**Date'):
            continue
        
        match = speaker_pattern.match(line_stripped)
        
        if match:
            # Save previous segment
            if current_text_lines:
                segments.append(TranscriptSegment(
                    start_time=current_time,
                    end_time=None,
                    speaker=current_speaker,
                    text=' '.join(current_text_lines)
                ))
                current_text_lines = []
            
            current_speaker = match.group(1).strip()
            current_time = match.group(2)
        else:
            # Content line (remove markdown formatting)
            clean_line = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', line_stripped)
            if clean_line:
                current_text_lines.append(clean_line)
    
    # Save last segment
    if current_text_lines:
        segments.append(TranscriptSegment(
            start_time=current_time,
            end_time=None,
            speaker=current_speaker,
            text=' '.join(current_text_lines)
        ))
    
    # If no segments detected, treat as plain text
    if not segments:
        return parse_plain(content)
    
    raw_text = _segments_to_text(segments)
    
    return ParsedTranscript(
        format=TranscriptFormat.TLDV,
        segments=segments,
        raw_text=raw_text,
        metadata={"segment_count": len(segments), "speakers": list(set(s.speaker for s in segments if s.speaker))}
    )


def parse_zoom_txt(content: str) -> ParsedTranscript:
    """
    Parse Zoom transcript TXT format.
    
    Format:
    [00:00:00] Speaker Name: Hello everyone
    [00:00:05] Another Speaker: Hi there
    """
    segments = []
    
    # Pattern for "[HH:MM:SS] Speaker: text"
    pattern = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.+)$')
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        match = pattern.match(line)
        if match:
            segments.append(TranscriptSegment(
                start_time=match.group(1),
                end_time=None,
                speaker=match.group(2).strip(),
                text=match.group(3).strip()
            ))
    
    # If no segments detected, treat as plain text
    if not segments:
        return parse_plain(content)
    
    raw_text = _segments_to_text(segments)
    
    return ParsedTranscript(
        format=TranscriptFormat.ZOOM_TXT,
        segments=segments,
        raw_text=raw_text,
        metadata={"segment_count": len(segments), "speakers": list(set(s.speaker for s in segments if s.speaker))}
    )


def parse_plain(content: str) -> ParsedTranscript:
    """
    Parse plain text (no special formatting).
    Treats the entire content as a single segment.
    """
    # Clean up the text
    clean_text = content.strip()
    
    segments = [TranscriptSegment(
        start_time=None,
        end_time=None,
        speaker=None,
        text=clean_text
    )]
    
    return ParsedTranscript(
        format=TranscriptFormat.PLAIN,
        segments=segments,
        raw_text=clean_text,
        metadata={"segment_count": 1}
    )


def _segments_to_text(segments: list[TranscriptSegment]) -> str:
    """
    Convert segments to clean text suitable for AI processing.
    Preserves speaker information for context.
    """
    lines = []
    for segment in segments:
        if segment.speaker:
            lines.append(f"{segment.speaker}: {segment.text}")
        else:
            lines.append(segment.text)
    
    return '\n\n'.join(lines)


def parse_transcript(content: str, filename: str = "") -> ParsedTranscript:
    """
    Main entry point for parsing transcripts.
    Automatically detects format and parses accordingly.
    
    Args:
        content: File content as string
        filename: Original filename (helps with format detection)
    
    Returns:
        ParsedTranscript object with segments and raw text
    """
    format_type = detect_format(content, filename)
    
    parsers = {
        TranscriptFormat.VTT: parse_vtt,
        TranscriptFormat.SRT: parse_srt,
        TranscriptFormat.OTTER: parse_otter,
        TranscriptFormat.TLDV: parse_tldv,
        TranscriptFormat.ZOOM_TXT: parse_zoom_txt,
        TranscriptFormat.PLAIN: parse_plain,
    }
    
    parser = parsers.get(format_type, parse_plain)
    return parser(content)


def get_supported_formats() -> list[dict]:
    """
    Returns list of supported transcript formats with descriptions.
    """
    return [
        {
            "format": "vtt",
            "name": "WebVTT",
            "extensions": [".vtt"],
            "description": "Zoom、YouTube、Google Meetの字幕形式",
            "example_source": "Zoom録画、YouTube字幕"
        },
        {
            "format": "srt",
            "name": "SubRip (SRT)",
            "extensions": [".srt"],
            "description": "標準的な字幕ファイル形式",
            "example_source": "各種動画プレーヤー"
        },
        {
            "format": "otter",
            "name": "Otter.ai",
            "extensions": [".txt"],
            "description": "Otter.aiからエクスポートしたテキスト",
            "example_source": "Otter.ai"
        },
        {
            "format": "tldv",
            "name": "tl;dv",
            "extensions": [".txt", ".md"],
            "description": "tl;dvからエクスポートしたテキスト",
            "example_source": "tl;dv"
        },
        {
            "format": "zoom_txt",
            "name": "Zoom TXT",
            "extensions": [".txt"],
            "description": "Zoomの文字起こしテキスト",
            "example_source": "Zoom"
        },
        {
            "format": "plain",
            "name": "プレーンテキスト",
            "extensions": [".txt", ".md"],
            "description": "通常のテキストファイル",
            "example_source": "手動入力"
        }
    ]

