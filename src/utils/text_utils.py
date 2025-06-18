"""
Text Utilities
Functions for parsing cut times files and text processing
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def parse_cuts_content(text_content: str, source_name: str = "Manual Input") -> Tuple[bool, str, Optional[Dict]]:
    """
    Central parser for cut times content (used by both file and manual input)
    
    Args:
        text_content: Raw text content with cut times
        source_name: Name of the source (for display purposes)
        
    Returns:
        Tuple of (is_valid, error_message, cuts_data)
    """
    if not text_content or not text_content.strip():
        return False, "Content is empty", None
    
    try:
        lines = text_content.strip().split('\n')
        
        # Validate all lines first
        valid_lines = 0
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            if _is_valid_time_line(line):
                valid_lines += 1
            else:
                return False, f"Invalid format on line {line_num}: '{line}'", None
        
        if valid_lines == 0:
            return False, "No valid time ranges found", None
        
        # Parse all lines
        cuts = []
        cut_index = 1
        
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            
            cut_data = _parse_cut_line(line, cut_index)
            if cut_data:
                cuts.append(cut_data)
                cut_index += 1
        
        cuts_data = {
            "cuts": cuts,
            "total_cuts": len(cuts),
            "source_file": source_name
        }
        
        return True, "", cuts_data
        
    except Exception as e:
        return False, f"Error parsing content: {str(e)}", None


def validate_and_parse_cuts_file(file_path: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validate and parse cut times file (wrapper that uses central parser)
    
    Args:
        file_path: Path to the cut times file
        
    Returns:
        Tuple of (is_valid, error_message, cuts_data)
    """
    if not file_path:
        return False, "No file selected", None
    
    try:
        path_obj = Path(file_path)
        
        # Basic file validation
        if not path_obj.exists():
            return False, "File does not exist", None
        
        if path_obj.suffix.lower() not in ['.txt', '.text']:
            return False, "Only text files (.txt) are supported", None
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Use central parser
        return parse_cuts_content(content, path_obj.name)
        
    except Exception as e:
        return False, f"Error processing cut times file: {str(e)}", None


def _is_valid_time_line(line: str) -> bool:
    """Check if a line has valid time format"""
    time_pattern = r'^\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}'
    return bool(re.match(time_pattern, line))


def _parse_cut_line(line: str, cut_index: int) -> Optional[Dict]:
    """Parse a single line into cut data"""
    try:
        # Split by ' - ' separator
        parts = [part.strip() for part in line.split(' - ')]
        
        if len(parts) < 2:
            return None
        
        start_time = parts[0]
        end_time = parts[1]
        
        # Validate time formats
        if not _is_valid_time_format(start_time) or not _is_valid_time_format(end_time):
            return None
        
        # Extract optional title and description
        title = parts[2] if len(parts) > 2 and parts[2] else f"Cut {cut_index}"
        description = parts[3] if len(parts) > 3 and parts[3] else f"Description {cut_index}"
        
        # Calculate duration
        duration = _calculate_duration(start_time, end_time)
        
        return {
            "id": cut_index,
            "start": start_time,
            "end": end_time,
            "title": title,
            "description": description,
            "duration": duration
        }
        
    except Exception as e:
        print(f"Error parsing line '{line}': {e}")
        return None


def _is_valid_time_format(time_str: str) -> bool:
    """Validate HH:MM:SS format"""
    pattern = r'^\d{2}:\d{2}:\d{2}$'
    if not re.match(pattern, time_str):
        return False
    
    try:
        parts = time_str.split(':')
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59
    except:
        return False


def _calculate_duration(start_time: str, end_time: str) -> str:
    """Calculate duration between start and end times"""
    try:
        start_seconds = _time_to_seconds(start_time)
        end_seconds = _time_to_seconds(end_time)
        
        if end_seconds <= start_seconds:
            return "00:00:00"  # Invalid range
        
        duration_seconds = end_seconds - start_seconds
        return _seconds_to_time(duration_seconds)
        
    except:
        return "00:00:00"


def _time_to_seconds(time_str: str) -> int:
    """Convert HH:MM:SS to total seconds"""
    parts = time_str.split(':')
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def _seconds_to_time(total_seconds: int) -> str:
    """Convert total seconds to HH:MM:SS format"""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_cuts_preview(cuts_data: Dict) -> str:
    """
    Format cuts data for preview display
    
    Args:
        cuts_data: Parsed cuts data
        
    Returns:
        Formatted string for display
    """
    if not cuts_data or 'cuts' not in cuts_data:
        return "No cuts data available"
    
    cuts = cuts_data['cuts']
    total = len(cuts)
    
    preview_lines = [f"📁 {cuts_data.get('source_file', 'Unknown file')}"]
    preview_lines.append(f"📊 Total cuts: {total}")
    preview_lines.append("")
    
    # Show first few cuts as preview
    max_preview = min(5, total)
    for i in range(max_preview):
        cut = cuts[i]
        line = f"{cut['start']} → {cut['end']} • {cut['title']}"
        preview_lines.append(line)
    
    if total > max_preview:
        preview_lines.append(f"... and {total - max_preview} more cuts")
    
    return "\n".join(preview_lines)
