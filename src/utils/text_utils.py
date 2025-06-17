"""
Text Utilities
Functions for parsing cut times files and text processing
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class CutTimesFile:
    """
    Cut times file handler that loads and parses text files with time ranges
    """
    
    def __init__(self, file_path: str):
        self.file_path = str(Path(file_path))
        self.path_obj = Path(file_path)
        self._content = None
        self._is_loaded = False
        self._parsed_cuts = None
        
    def __enter__(self):
        """Context manager entry"""
        self.load()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        
    def load(self):
        """Load the text file content"""
        if self._is_loaded:
            return
            
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self._content = file.read()
            self._is_loaded = True
        except Exception as e:
            raise RuntimeError(f"Failed to load cut times file: {e}")
    
    def release(self):
        """Release resources"""
        self._content = None
        self._is_loaded = False
        self._parsed_cuts = None
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate if the file is a valid cut times file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not self.path_obj.exists():
            return False, "File does not exist"
        
        # Check file extension (accept .txt files)
        if self.path_obj.suffix.lower() not in ['.txt', '.text']:
            return False, "Only text files (.txt) are supported"
        
        # Ensure content is loaded
        if not self._is_loaded:
            self.load()
        
        if not self._content:
            return False, "File is empty"
        
        # Validate at least one valid time range line
        lines = self._content.strip().split('\n')
        valid_lines = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            if self._is_valid_time_line(line):
                valid_lines += 1
            else:
                return False, f"Invalid format on line {line_num}: '{line}'"
        
        if valid_lines == 0:
            return False, "No valid time ranges found in file"
        
        return True, ""
    
    def _is_valid_time_line(self, line: str) -> bool:
        """Check if a line has valid time format"""
        # Basic pattern: HH:MM:SS - HH:MM:SS (with optional title and description)
        time_pattern = r'^\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}'
        return bool(re.match(time_pattern, line))
    
    def parse_content(self) -> Optional[Dict]:
        """
        Parse the content and convert to cuts data structure
        
        Returns:
            Dictionary with cuts data or None if parsing fails
        """
        if not self._is_loaded or not self._content:
            return None
        
        try:
            lines = self._content.strip().split('\n')
            cuts = []
            cut_index = 1
            
            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                cut_data = self._parse_cut_line(line, cut_index)
                if cut_data:
                    cuts.append(cut_data)
                    cut_index += 1
            
            self._parsed_cuts = {
                "cuts": cuts,
                "total_cuts": len(cuts),
                "source_file": self.path_obj.name
            }
            
            return self._parsed_cuts
            
        except Exception as e:
            print(f"Error parsing cut times content: {e}")
            return None
    
    def _parse_cut_line(self, line: str, cut_index: int) -> Optional[Dict]:
        """Parse a single line into cut data"""
        try:
            # Split by ' - ' separator
            parts = [part.strip() for part in line.split(' - ')]
            
            if len(parts) < 2:
                return None
            
            start_time = parts[0]
            end_time = parts[1]
            
            # Validate time formats
            if not self._is_valid_time_format(start_time) or not self._is_valid_time_format(end_time):
                return None
            
            # Extract optional title and description
            title = parts[2] if len(parts) > 2 and parts[2] else f"Cut {cut_index}"
            description = parts[3] if len(parts) > 3 and parts[3] else f"Description {cut_index}"
            
            # Calculate duration
            duration = self._calculate_duration(start_time, end_time)
            
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
    
    def _is_valid_time_format(self, time_str: str) -> bool:
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
    
    def _calculate_duration(self, start_time: str, end_time: str) -> str:
        """Calculate duration between start and end times"""
        try:
            start_seconds = self._time_to_seconds(start_time)
            end_seconds = self._time_to_seconds(end_time)
            
            if end_seconds <= start_seconds:
                return "00:00:00"  # Invalid range
            
            duration_seconds = end_seconds - start_seconds
            return self._seconds_to_time(duration_seconds)
            
        except:
            return "00:00:00"
    
    def _time_to_seconds(self, time_str: str) -> int:
        """Convert HH:MM:SS to total seconds"""
        parts = time_str.split(':')
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def _seconds_to_time(self, total_seconds: int) -> str:
        """Convert total seconds to HH:MM:SS format"""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def validate_and_parse_cuts_file(file_path: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    Validate and parse cut times file in a single operation (most efficient)
    
    Args:
        file_path: Path to the cut times file
        
    Returns:
        Tuple of (is_valid, error_message, cuts_data)
    """
    if not file_path:
        return False, "No file selected", None
    
    try:
        with CutTimesFile(file_path) as cuts_file:
            is_valid, error_msg = cuts_file.validate()
            if not is_valid:
                return False, error_msg, None
            
            cuts_data = cuts_file.parse_content()
            if not cuts_data:
                return False, "Failed to parse file content", None
            
            return True, "", cuts_data
            
    except Exception as e:
        return False, f"Error processing cut times file: {str(e)}", None


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
