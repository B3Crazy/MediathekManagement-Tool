#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dependency Checker
Checks and installs all required dependencies for the MediathekManagement-Tool
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Tuple, List, Dict


class DependencyChecker:
    """Comprehensive dependency checker and installer"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.missing_dependencies = []
        self.outdated_packages = []
        
    @staticmethod
    def _setup_logging() -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        return logging.getLogger(__name__)
    
    def check_python_version(self) -> bool:
        """Check if Python version is 3.8 or higher"""
        self.logger.info("🔍 Checking Python version...")
        version = sys.version_info
        
        if version.major >= 3 and version.minor >= 8:
            self.logger.info(f"✓ Python {version.major}.{version.minor}.{version.micro} found")
            return True
        else:
            self.logger.error(f"✗ Python version too old: {version.major}.{version.minor}")
            self.logger.error("  Python 3.8 or higher is required!")
            return False
    
    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed"""
        self.logger.info("🔍 Checking ffmpeg...")
        
        if shutil.which("ffmpeg"):
            try:
                result = subprocess.run(
                    ["ffmpeg", "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    self.logger.info(f"✓ ffmpeg found: {version_line}")
                    return True
            except Exception as e:
                self.logger.warning(f"⚠ ffmpeg found but error checking version: {e}")
                return True
        
        self.logger.warning("✗ ffmpeg not found")
        self.missing_dependencies.append("ffmpeg")
        return False
    
    def install_ffmpeg_instructions(self):
        """Provide instructions to install ffmpeg"""
        self.logger.info("\n" + "="*60)
        self.logger.info("📦 FFMPEG INSTALLATION REQUIRED")
        self.logger.info("="*60)
        self.logger.info("\nffmpeg is required for video processing.")
        self.logger.info("\nWindows installation options:")
        self.logger.info("1. Using Chocolatey (recommended):")
        self.logger.info("   choco install ffmpeg")
        self.logger.info("\n2. Using Scoop:")
        self.logger.info("   scoop install ffmpeg")
        self.logger.info("\n3. Manual installation:")
        self.logger.info("   Download from: https://www.gyan.dev/ffmpeg/builds/")
        self.logger.info("   Extract and add to PATH")
        self.logger.info("="*60 + "\n")
        
        # Try to install with choco if available
        if shutil.which("choco"):
            response = input("Try to install ffmpeg with Chocolatey now? (y/n): ")
            if response.lower() == 'y':
                try:
                    subprocess.run(["choco", "install", "ffmpeg", "-y"], check=True)
                    self.logger.info("✓ ffmpeg installed successfully")
                    return True
                except Exception as e:
                    self.logger.error(f"✗ Failed to install ffmpeg: {e}")
        
        return False
    
    def check_pip(self) -> bool:
        """Check if pip is installed"""
        self.logger.info("🔍 Checking pip...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.logger.info(f"✓ pip found: {result.stdout.strip()}")
                return True
        except Exception as e:
            self.logger.error(f"✗ pip not found: {e}")
            return False
        
        return False
    
    def upgrade_pip(self) -> bool:
        """Upgrade pip to latest version"""
        self.logger.info("⬆️  Upgrading pip...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self.logger.info("✓ pip upgraded successfully")
                return True
            else:
                self.logger.warning(f"⚠ pip upgrade had issues: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Failed to upgrade pip: {e}")
            return False
    
    def check_python_packages(self, requirements_file: str) -> bool:
        """Check if all required Python packages are installed"""
        self.logger.info(f"🔍 Checking Python packages from {requirements_file}...")
        
        if not os.path.exists(requirements_file):
            self.logger.warning(f"⚠ Requirements file not found: {requirements_file}")
            return True
        
        # Read requirements
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [
                line.strip() for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        # Check each package
        missing = []
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].split('[')[0].strip()
            if not self._is_package_installed(package_name):
                missing.append(req)
        
        if missing:
            self.logger.warning(f"✗ Missing packages: {', '.join(missing)}")
            return False
        else:
            self.logger.info(f"✓ All packages from {Path(requirements_file).name} are installed")
            return True
    
    def _is_package_installed(self, package_name: str) -> bool:
        """Check if a specific package is installed"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def install_python_packages(self, requirements_file: str) -> bool:
        """Install Python packages from requirements file"""
        self.logger.info(f"📦 Installing packages from {requirements_file}...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                timeout=300
            )
            if result.returncode == 0:
                self.logger.info(f"✓ Successfully installed packages from {Path(requirements_file).name}")
                return True
            else:
                self.logger.error(f"✗ Failed to install packages from {Path(requirements_file).name}")
                return False
        except Exception as e:
            self.logger.error(f"✗ Error installing packages: {e}")
            return False
    
    def update_python_packages(self, requirements_file: str) -> bool:
        """Update all Python packages to latest versions"""
        self.logger.info(f"⬆️  Updating packages from {requirements_file}...")
        
        if not os.path.exists(requirements_file):
            return True
        
        # Read requirements
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [
                line.strip() for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        updated = []
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].split('[')[0].strip()
            
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if "Successfully installed" in result.stdout:
                    updated.append(package_name)
                    self.logger.info(f"  ✓ Updated {package_name}")
                else:
                    self.logger.info(f"  ✓ {package_name} already up-to-date")
                    
            except Exception as e:
                self.logger.warning(f"  ⚠ Failed to update {package_name}: {e}")
        
        if updated:
            self.logger.info(f"✓ Updated {len(updated)} package(s): {', '.join(updated)}")
        else:
            self.logger.info("✓ All packages are up-to-date")
        
        return True
    
    def check_all_dependencies(self) -> bool:
        """Run all dependency checks"""
        self.logger.info("\n" + "="*60)
        self.logger.info("🚀 MEDIATHEKMANAGEMENT-TOOL DEPENDENCY CHECK")
        self.logger.info("="*60 + "\n")
        
        all_ok = True
        
        # Check Python version
        if not self.check_python_version():
            all_ok = False
            return False
        
        print()
        
        # Check pip
        if not self.check_pip():
            all_ok = False
            self.logger.error("pip is required but not found!")
            return False
        
        print()
        
        # Upgrade pip
        self.upgrade_pip()
        print()
        
        # Check ffmpeg
        if not self.check_ffmpeg():
            all_ok = False
            self.install_ffmpeg_instructions()
            # Continue anyway, user might install ffmpeg later
        
        print()
        
        # Check and install Python packages
        project_root = Path(__file__).parent.parent
        requirements_files = [
            project_root / "requirements.txt",
            project_root / "backend" / "requirements.txt"
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                if not self.check_python_packages(str(req_file)):
                    self.logger.info(f"📦 Installing missing packages from {req_file.name}...")
                    if not self.install_python_packages(str(req_file)):
                        all_ok = False
                print()
        
        # Update packages
        self.logger.info("🔄 Checking for package updates...")
        for req_file in requirements_files:
            if req_file.exists():
                self.update_python_packages(str(req_file))
        
        print()
        
        # Summary
        self.logger.info("="*60)
        if all_ok and not self.missing_dependencies:
            self.logger.info("✅ ALL DEPENDENCIES SATISFIED!")
        else:
            self.logger.warning("⚠️  SOME DEPENDENCIES MISSING")
            if self.missing_dependencies:
                self.logger.warning(f"Missing: {', '.join(self.missing_dependencies)}")
        self.logger.info("="*60 + "\n")
        
        return all_ok
    
    def run(self) -> bool:
        """Main entry point"""
        return self.check_all_dependencies()


def main():
    """Main function"""
    checker = DependencyChecker()
    success = checker.run()
    
    if not success:
        print("\nPress Enter to continue anyway or Ctrl+C to abort...")
        try:
            input()
        except KeyboardInterrupt:
            print("\nAborted by user.")
            sys.exit(1)
    
    return success


if __name__ == "__main__":
    main()
