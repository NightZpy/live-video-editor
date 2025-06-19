"""
Data Cache Manager
Handles saving and loading of transcriptions and cuts data for recovery
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple


class DataCacheManager:
    """
    Manages caching of transcription and cuts data for recovery purposes
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize the cache manager
        
        Args:
            workspace_root: Root directory of the workspace (defaults to current directory)
        """
        if workspace_root is None:
            workspace_root = os.getcwd()
            
        self.workspace_root = Path(workspace_root)
        self.data_dir = self.workspace_root / "data"
        self.transcriptions_dir = self.data_dir / "transcriptions"
        self.cuts_dir = self.data_dir / "cuts"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        self.transcriptions_dir.mkdir(parents=True, exist_ok=True)
        self.cuts_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Cache directories ready:")
        print(f"   📝 Transcriptions: {self.transcriptions_dir}")
        print(f"   ✂️ Cuts: {self.cuts_dir}")
    
    def _get_video_name(self, video_path: str) -> str:
        """
        Extract video name without extension from path
        
        Args:
            video_path: Full path to video file
            
        Returns:
            Video name without extension
        """
        return Path(video_path).stem
    
    def save_transcription(self, video_path: str, transcription_data: Dict, video_info: Dict) -> str:
        """
        Save transcription data to cache
        
        Args:
            video_path: Path to the video file
            transcription_data: Complete transcription result from Whisper
            video_info: Video metadata
            
        Returns:
            Path to saved transcription file
        """
        video_name = self._get_video_name(video_path)
        transcription_file = self.transcriptions_dir / f"{video_name}.json"
        
        # Build enhanced transcription data with metadata
        cache_data = {
            "transcription": transcription_data,
            "video_info": video_info,
            "video_path": str(Path(video_path).resolve()),
            "created_at": datetime.now().isoformat(),
            "cache_version": "1.0"
        }
        
        try:
            with open(transcription_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Transcription saved: {transcription_file}")
            return str(transcription_file)
            
        except Exception as e:
            print(f"❌ Failed to save transcription: {e}")
            raise
    
    def save_cuts(self, video_path: str, cuts_data: Dict, processing_info: Optional[Dict] = None) -> str:
        """
        Save cuts data to cache (this is the final processed format)
        
        Args:
            video_path: Path to the video file
            cuts_data: Final cuts data in application format
            processing_info: Additional info about the processing (model used, etc.)
            
        Returns:
            Path to saved cuts file
        """
        video_name = self._get_video_name(video_path)
        cuts_file = self.cuts_dir / f"{video_name}.json"
        
        # Build enhanced cuts data with metadata
        cache_data = {
            "cuts_data": cuts_data,
            "video_path": str(Path(video_path).resolve()),
            "created_at": datetime.now().isoformat(),
            "processing_info": processing_info or {},
            "cache_version": "1.0"
        }
        
        try:
            with open(cuts_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Cuts data saved: {cuts_file}")
            print(f"   📊 Total cuts: {cuts_data.get('video_info', {}).get('total_cuts', 0)}")
            return str(cuts_file)
            
        except Exception as e:
            print(f"❌ Failed to save cuts: {e}")
            raise
    
    def load_transcription(self, video_path: str) -> Optional[Tuple[Dict, Dict]]:
        """
        Load cached transcription data
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Tuple of (transcription_data, video_info) if found, None otherwise
        """
        video_name = self._get_video_name(video_path)
        transcription_file = self.transcriptions_dir / f"{video_name}.json"
        
        if not transcription_file.exists():
            return None
        
        try:
            with open(transcription_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"📂 Loaded cached transcription: {transcription_file}")
            print(f"   🕒 Created: {cache_data.get('created_at', 'Unknown')}")
            
            return cache_data.get('transcription'), cache_data.get('video_info')
            
        except Exception as e:
            print(f"⚠️ Failed to load transcription cache: {e}")
            return None
    
    def load_cuts(self, video_path: str) -> Optional[Dict]:
        """
        Load cached cuts data
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Cuts data if found, None otherwise
        """
        video_name = self._get_video_name(video_path)
        cuts_file = self.cuts_dir / f"{video_name}.json"
        
        if not cuts_file.exists():
            return None
        
        try:
            with open(cuts_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"📂 Loaded cached cuts: {cuts_file}")
            print(f"   🕒 Created: {cache_data.get('created_at', 'Unknown')}")
            print(f"   📊 Total cuts: {cache_data.get('cuts_data', {}).get('video_info', {}).get('total_cuts', 0)}")
            
            return cache_data.get('cuts_data')
            
        except Exception as e:
            print(f"⚠️ Failed to load cuts cache: {e}")
            return None
    
    def has_transcription_cache(self, video_path: str) -> bool:
        """Check if transcription cache exists for video"""
        video_name = self._get_video_name(video_path)
        transcription_file = self.transcriptions_dir / f"{video_name}.json"
        return transcription_file.exists()
    
    def has_cuts_cache(self, video_path: str) -> bool:
        """Check if cuts cache exists for video"""
        video_name = self._get_video_name(video_path)
        cuts_file = self.cuts_dir / f"{video_name}.json"
        return cuts_file.exists()
    
    def clear_cache(self, video_path: Optional[str] = None):
        """
        Clear cache for specific video or all cache
        
        Args:
            video_path: If provided, clear only this video's cache. If None, clear all.
        """
        if video_path:
            video_name = self._get_video_name(video_path)
            
            # Remove transcription cache
            transcription_file = self.transcriptions_dir / f"{video_name}.json"
            if transcription_file.exists():
                transcription_file.unlink()
                print(f"🗑️ Removed transcription cache: {transcription_file}")
            
            # Remove cuts cache
            cuts_file = self.cuts_dir / f"{video_name}.json"
            if cuts_file.exists():
                cuts_file.unlink()
                print(f"🗑️ Removed cuts cache: {cuts_file}")
        else:
            # Clear all cache
            import shutil
            if self.data_dir.exists():
                shutil.rmtree(self.data_dir)
                self._ensure_directories()
                print(f"🗑️ Cleared all cache data")
