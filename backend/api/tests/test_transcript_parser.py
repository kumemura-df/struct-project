"""
Tests for transcript parser service.
"""

import pytest
from services.transcript_parser import (
    parse_transcript,
    parse_vtt,
    parse_srt,
    parse_otter,
    parse_tldv,
    parse_zoom_txt,
    detect_format,
    TranscriptFormat,
    get_supported_formats,
)


class TestFormatDetection:
    """Test format detection."""
    
    def test_detect_vtt_by_extension(self):
        assert detect_format("", "meeting.vtt") == TranscriptFormat.VTT
    
    def test_detect_srt_by_extension(self):
        assert detect_format("", "meeting.srt") == TranscriptFormat.SRT
    
    def test_detect_vtt_by_content(self):
        content = "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nHello world"
        assert detect_format(content, "") == TranscriptFormat.VTT
    
    def test_detect_srt_by_content(self):
        content = "1\n00:00:00,000 --> 00:00:05,000\nHello world"
        assert detect_format(content, "") == TranscriptFormat.SRT
    
    def test_detect_zoom_txt(self):
        content = "[00:00:00] Speaker Name: Hello everyone"
        assert detect_format(content, "") == TranscriptFormat.ZOOM_TXT
    
    def test_detect_plain_default(self):
        content = "Just some regular text without any special formatting."
        assert detect_format(content, "") == TranscriptFormat.PLAIN


class TestVTTParser:
    """Test VTT format parsing."""
    
    def test_parse_simple_vtt(self):
        content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello everyone, welcome to the meeting.

00:00:05.000 --> 00:00:10.000
Let's discuss the project status.
"""
        result = parse_vtt(content)
        
        assert result.format == TranscriptFormat.VTT
        assert len(result.segments) == 2
        assert result.segments[0].text == "Hello everyone, welcome to the meeting."
        assert result.segments[0].start_time == "00:00:00.000"
    
    def test_parse_vtt_with_speaker(self):
        content = """WEBVTT

00:00:00.000 --> 00:00:05.000
John: Hello everyone

00:00:05.000 --> 00:00:10.000
Jane: Hi John
"""
        result = parse_vtt(content)
        
        assert len(result.segments) == 2
        assert result.segments[0].speaker == "John"
        assert result.segments[0].text == "Hello everyone"
        assert result.segments[1].speaker == "Jane"


class TestSRTParser:
    """Test SRT format parsing."""
    
    def test_parse_simple_srt(self):
        content = """1
00:00:00,000 --> 00:00:05,000
Hello everyone

2
00:00:05,000 --> 00:00:10,000
Welcome to the meeting
"""
        result = parse_srt(content)
        
        assert result.format == TranscriptFormat.SRT
        assert len(result.segments) == 2
        assert result.segments[0].text == "Hello everyone"
        assert result.segments[1].text == "Welcome to the meeting"
    
    def test_parse_srt_with_multiline_text(self):
        content = """1
00:00:00,000 --> 00:00:05,000
This is a long sentence
that spans multiple lines

2
00:00:05,000 --> 00:00:10,000
Another segment
"""
        result = parse_srt(content)
        
        assert len(result.segments) == 2
        assert "spans multiple lines" in result.segments[0].text


class TestOtterParser:
    """Test Otter.ai format parsing."""
    
    def test_parse_otter_format(self):
        content = """田中太郎  0:00
本日はプロジェクトの進捗確認を行います。

鈴木花子  0:15
はい、現在のステータスを報告します。
API開発は順調に進んでいます。
"""
        result = parse_otter(content)
        
        assert result.format == TranscriptFormat.OTTER
        assert len(result.segments) == 2
        assert result.segments[0].speaker == "田中太郎"
        assert "進捗確認" in result.segments[0].text
        assert result.segments[1].speaker == "鈴木花子"
    
    def test_parse_otter_with_timestamps(self):
        content = """Speaker A  00:00:00
First message

Speaker B  00:01:30
Second message
"""
        result = parse_otter(content)
        
        assert len(result.segments) == 2
        assert result.segments[0].start_time == "00:00:00"
        assert result.segments[1].start_time == "00:01:30"


class TestTldvParser:
    """Test tl;dv format parsing."""
    
    def test_parse_tldv_format(self):
        content = """## Meeting Notes
**Date:** 2024-12-08

### Transcript

**John Smith** (00:00:00)
Let's start with the agenda.

**Jane Doe** (00:01:15)
I'll share my screen now.
"""
        result = parse_tldv(content)
        
        assert result.format == TranscriptFormat.TLDV
        assert len(result.segments) == 2
        assert result.segments[0].speaker == "John Smith"
        assert result.segments[0].text == "Let's start with the agenda."


class TestZoomTxtParser:
    """Test Zoom TXT format parsing."""
    
    def test_parse_zoom_txt(self):
        content = """[00:00:00] Host: Welcome everyone to today's meeting.
[00:00:10] Participant 1: Thanks for having us.
[00:00:20] Participant 2: Good morning!
"""
        result = parse_zoom_txt(content)
        
        assert result.format == TranscriptFormat.ZOOM_TXT
        assert len(result.segments) == 3
        assert result.segments[0].speaker == "Host"
        assert result.segments[0].text == "Welcome everyone to today's meeting."
        assert result.segments[0].start_time == "00:00:00"


class TestParseTranscript:
    """Test main parse_transcript function."""
    
    def test_auto_detect_and_parse_vtt(self):
        content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Test message
"""
        result = parse_transcript(content, "meeting.vtt")
        
        assert result.format == TranscriptFormat.VTT
        assert len(result.segments) == 1
    
    def test_auto_detect_and_parse_srt(self):
        content = """1
00:00:00,000 --> 00:00:05,000
Test message
"""
        result = parse_transcript(content, "subtitle.srt")
        
        assert result.format == TranscriptFormat.SRT
        assert len(result.segments) == 1
    
    def test_raw_text_generation(self):
        content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Speaker A: First message

00:00:05.000 --> 00:00:10.000
Speaker B: Second message
"""
        result = parse_transcript(content, "test.vtt")
        
        assert "Speaker A: First message" in result.raw_text
        assert "Speaker B: Second message" in result.raw_text
    
    def test_plain_text_fallback(self):
        content = "This is just regular meeting notes without any formatting."
        result = parse_transcript(content, "notes.txt")
        
        assert result.format == TranscriptFormat.PLAIN
        assert result.raw_text == content


class TestSupportedFormats:
    """Test get_supported_formats function."""
    
    def test_returns_format_list(self):
        formats = get_supported_formats()
        
        assert isinstance(formats, list)
        assert len(formats) >= 5  # VTT, SRT, Otter, tl;dv, Zoom, Plain
        
        # Check structure
        for fmt in formats:
            assert "format" in fmt
            assert "name" in fmt
            assert "extensions" in fmt
            assert "description" in fmt


class TestJapaneseContent:
    """Test parsing of Japanese content."""
    
    def test_japanese_vtt(self):
        content = """WEBVTT

00:00:00.000 --> 00:00:05.000
田中: プロジェクトの進捗を確認しましょう。

00:00:05.000 --> 00:00:10.000
鈴木: はい、現在の状況を報告します。
"""
        result = parse_vtt(content)
        
        assert len(result.segments) == 2
        assert result.segments[0].speaker == "田中"
        assert "進捗を確認" in result.segments[0].text
    
    def test_japanese_otter(self):
        content = """プロジェクトマネージャー  0:00
今日はリスクについて話し合います。

開発リーダー  0:30
はい、現在いくつかの懸念事項があります。
スケジュールが厳しいかもしれません。
"""
        result = parse_otter(content)
        
        assert len(result.segments) == 2
        assert "リスク" in result.segments[0].text
        assert "懸念事項" in result.segments[1].text

