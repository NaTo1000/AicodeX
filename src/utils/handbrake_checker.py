"""
HandBrake version checker utility
Checks and downloads the latest HandBrake version
"""

import hashlib
import urllib.request
import os


class HandBrakeChecker:
    """Utility class for checking HandBrake versions"""
    
    LATEST_VERSION = "1.10.2"
    DOWNLOAD_URL = "https://github.com/HandBrake/HandBrake/releases/download/1.10.2/HandBrake-1.10.2-x86_64-Win_GUI.exe"
    EXPECTED_SHA256 = "ff868bb43c19a4fd8bec8f4b9d83a756f6818cf4b229012715f35eb2416673cd"
    
    def __init__(self):
        """Initialize HandBrake checker"""
        self.version = self.LATEST_VERSION
        
    def check_version(self):
        """Check the latest HandBrake version"""
        return f"Latest HandBrake version: {self.LATEST_VERSION}\nDownload URL: {self.DOWNLOAD_URL}"
        
    def download(self, destination_path=None):
        """Download HandBrake installer"""
        if destination_path is None:
            destination_path = f"HandBrake-{self.LATEST_VERSION}-x86_64-Win_GUI.exe"
            
        try:
            print(f"Downloading HandBrake {self.LATEST_VERSION}...")
            urllib.request.urlretrieve(self.DOWNLOAD_URL, destination_path)
            
            # Verify SHA256 checksum
            if self.verify_checksum(destination_path):
                print(f"Download complete: {destination_path}")
                print("SHA256 checksum verified successfully!")
                return True
            else:
                print("SHA256 checksum verification failed!")
                os.remove(destination_path)
                return False
        except Exception as e:
            print(f"Error downloading HandBrake: {e}")
            return False
            
    def verify_checksum(self, file_path):
        """Verify SHA256 checksum of downloaded file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            calculated_hash = sha256_hash.hexdigest()
            return calculated_hash.lower() == self.EXPECTED_SHA256.lower()
        except Exception as e:
            print(f"Error verifying checksum: {e}")
            return False
            
    def get_info(self):
        """Get HandBrake information"""
        return {
            "version": self.LATEST_VERSION,
            "download_url": self.DOWNLOAD_URL,
            "sha256": self.EXPECTED_SHA256
        }
