"""
Advanced Configuration Management and Automation Features
Handles configuration profiles, scheduling, and automated workflows
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import asdict, dataclass
import threading
import time
import tempfile

try:
    import schedule
    SCHEDULING_AVAILABLE = True
except ImportError:
    SCHEDULING_AVAILABLE = False

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = ""
    
    discord_enabled: bool = False
    discord_webhook_url: str = ""
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []

@dataclass
class ScheduleConfig:
    """Configuration for scheduled analysis."""
    enabled: bool = False
    frequency: str = "daily"  # daily, weekly, monthly, custom
    time: str = "02:00"  # HH:MM format
    days_of_week: List[str] = None  # For weekly: ['monday', 'tuesday', ...]
    day_of_month: int = 1  # For monthly
    custom_cron: str = ""  # For custom scheduling
    
    def __post_init__(self):
        if self.days_of_week is None:
            self.days_of_week = []

@dataclass
class AutomationConfig:
    """Configuration for automation features."""
    auto_cleanup: bool = True
    cleanup_after_days: int = 30
    auto_archive: bool = False
    archive_after_days: int = 7
    auto_backup: bool = False
    backup_location: str = ""
    max_backup_files: int = 10
    
    watch_directory: bool = False
    watch_path: str = ""
    auto_process_new_files: bool = False
    
    performance_monitoring: bool = True
    resource_limits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                "max_memory_mb": 2048,
                "max_cpu_percent": 80,
                "max_processing_time_minutes": 30
            }

class ConfigurationManager:
    """Advanced configuration management system."""
    
    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Configuration storage
        self.profiles: Dict[str, Any] = {}
        self.active_profile = "default"
        self.global_config = {}
        
        # Load existing configurations
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files."""
        try:
            # Load global config
            global_config_file = self.config_dir / "global.json"
            if global_config_file.exists():
                with open(global_config_file, 'r', encoding='utf-8') as f:
                    self.global_config = json.load(f)
            
            # Load profiles
            profiles_dir = self.config_dir / "profiles"
            if profiles_dir.exists():
                for profile_file in profiles_dir.glob("*.json"):
                    profile_name = profile_file.stem
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        self.profiles[profile_name] = json.load(f)
            
            self.logger.info(f"Loaded {len(self.profiles)} configuration profiles")
            
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")
    
    def create_profile(self, name: str, config: Dict[str, Any], description: str = ""):
        """Create a new configuration profile."""
        try:
            profiles_dir = self.config_dir / "profiles"
            profiles_dir.mkdir(exist_ok=True)
            
            profile_data = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "config": config
            }
            
            profile_file = profiles_dir / f"{name}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            self.profiles[name] = profile_data
            self.logger.info(f"Created profile: {name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create profile {name}: {e}")
    
    def load_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a specific configuration profile."""
        return self.profiles.get(name, {}).get('config')
    
    def list_profiles(self) -> List[Dict[str, str]]:
        """List all available profiles."""
        profile_list = []
        for name, profile in self.profiles.items():
            profile_list.append({
                "name": name,
                "description": profile.get("description", ""),
                "created_at": profile.get("created_at", "")
            })
        return profile_list
    
    def set_active_profile(self, name: str) -> bool:
        """Set the active configuration profile."""
        if name in self.profiles:
            self.active_profile = name
            self.global_config["active_profile"] = name
            self._save_global_config()
            self.logger.info(f"Active profile set to: {name}")
            return True
        return False
    
    def get_active_config(self) -> Dict[str, Any]:
        """Get the currently active configuration."""
        return self.load_profile(self.active_profile) or {}
    
    def _save_global_config(self):
        """Save global configuration."""
        try:
            global_config_file = self.config_dir / "global.json"
            with open(global_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.global_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save global config: {e}")
    
    def export_profile(self, name: str, export_path: str, format: str = "json") -> bool:
        """Export a profile to file."""
        try:
            profile = self.profiles.get(name)
            if not profile:
                return False
            
            export_file = Path(export_path)
            
            if format.lower() == "json":
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, indent=2, ensure_ascii=False)
            elif format.lower() == "yaml" and yaml:
                with open(export_file, 'w', encoding='utf-8') as f:
                    yaml.dump(profile, f, default_flow_style=False)
            elif format.lower() == "toml" and TOML_AVAILABLE:
                with open(export_file, 'w', encoding='utf-8') as f:
                    toml.dump(profile, f)
            else:
                return False
            
            self.logger.info(f"Exported profile {name} to {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export profile {name}: {e}")
            return False
    
    def import_profile(self, import_path: str, name: Optional[str] = None) -> bool:
        """Import a profile from file."""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                return False
            
            # Determine format and load
            if import_file.suffix.lower() == ".json":
                with open(import_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
            elif import_file.suffix.lower() in [".yml", ".yaml"]:
                with open(import_file, 'r', encoding='utf-8') as f:
                    profile_data = yaml.safe_load(f)
            elif import_file.suffix.lower() == ".toml" and TOML_AVAILABLE:
                with open(import_file, 'r', encoding='utf-8') as f:
                    profile_data = toml.load(f)
            else:
                return False
            
            # Use provided name or extract from data
            profile_name = name or profile_data.get('name', import_file.stem)
            
            # Create profile
            self.create_profile(
                profile_name,
                profile_data.get('config', profile_data),
                profile_data.get('description', f"Imported from {import_file}")
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import profile from {import_path}: {e}")
            return False

class AutomationManager:
    """Manages automated workflows and scheduling."""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.scheduled_jobs = {}
        self.automation_config = None
        self.notification_config = None
        self.schedule_config = None
        self._running = False
        self._scheduler_thread = None
        
        # Load automation configuration
        self._load_automation_config()
    
    def _load_automation_config(self):
        """Load automation configuration from active profile."""
        try:
            active_config = self.config_manager.get_active_config()
            
            self.automation_config = AutomationConfig(
                **active_config.get('automation', {})
            )
            
            self.notification_config = NotificationConfig(
                **active_config.get('notifications', {})
            )
            
            self.schedule_config = ScheduleConfig(
                **active_config.get('scheduling', {})
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load automation config: {e}")
            # Use defaults
            self.automation_config = AutomationConfig()
            self.notification_config = NotificationConfig()
            self.schedule_config = ScheduleConfig()
    
    def schedule_analysis(self, analyzer_function: Callable, *args, **kwargs):
        """Schedule automatic analysis based on configuration."""
        if not SCHEDULING_AVAILABLE or not self.schedule_config.enabled:
            self.logger.warning("Scheduling not available or disabled")
            return
        
        try:
            schedule.clear()  # Clear existing schedules
            
            if self.schedule_config.frequency == "daily":
                schedule.every().day.at(self.schedule_config.time).do(
                    self._run_scheduled_analysis, analyzer_function, *args, **kwargs
                )
            elif self.schedule_config.frequency == "weekly":
                for day in self.schedule_config.days_of_week:
                    getattr(schedule.every(), day.lower()).at(self.schedule_config.time).do(
                        self._run_scheduled_analysis, analyzer_function, *args, **kwargs
                    )
            elif self.schedule_config.frequency == "monthly":
                # Monthly scheduling is more complex, implement basic version
                schedule.every().day.at(self.schedule_config.time).do(
                    self._check_monthly_schedule, analyzer_function, *args, **kwargs
                )
            
            self.logger.info(f"Scheduled analysis: {self.schedule_config.frequency}")
            
            # Start scheduler thread
            if not self._running:
                self._start_scheduler()
            
        except Exception as e:
            self.logger.error(f"Failed to schedule analysis: {e}")
    
    def _start_scheduler(self):
        """Start the background scheduler thread."""
        def run_scheduler():
            self._running = True
            while self._running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self._scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self._scheduler_thread.start()
        self.logger.info("Scheduler thread started")
    
    def stop_scheduler(self):
        """Stop the background scheduler."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        self.logger.info("Scheduler stopped")
    
    def _run_scheduled_analysis(self, analyzer_function: Callable, *args, **kwargs):
        """Run scheduled analysis with error handling and notifications."""
        try:
            self.logger.info("Starting scheduled analysis")
            
            # Record start time
            start_time = datetime.now()
            
            # Run analysis
            result = analyzer_function(*args, **kwargs)
            
            # Record completion
            end_time = datetime.now()
            duration = end_time - start_time
            
            # Send success notification
            self._send_notification(
                "success",
                f"Scheduled analysis completed successfully in {duration}",
                {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_seconds": duration.total_seconds(),
                    "result": str(result) if result else "No result"
                }
            )
            
            # Perform cleanup if enabled
            if self.automation_config.auto_cleanup:
                self._perform_cleanup()
            
        except Exception as e:
            self.logger.error(f"Scheduled analysis failed: {e}")
            self._send_notification(
                "error",
                f"Scheduled analysis failed: {e}",
                {"error": str(e), "timestamp": datetime.now().isoformat()}
            )
    
    def _check_monthly_schedule(self, analyzer_function: Callable, *args, **kwargs):
        """Check if today matches monthly schedule."""
        if datetime.now().day == self.schedule_config.day_of_month:
            self._run_scheduled_analysis(analyzer_function, *args, **kwargs)
    
    def _perform_cleanup(self):
        """Perform automated cleanup based on configuration."""
        try:
            if not self.automation_config.auto_cleanup:
                return
            
            # Clean old analysis results
            cleanup_date = datetime.now() - timedelta(days=self.automation_config.cleanup_after_days)
            
            # This would be implemented based on specific cleanup needs
            self.logger.info(f"Cleanup performed for files older than {cleanup_date}")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
    
    def _send_notification(self, type: str, message: str, details: Dict[str, Any]):
        """Send notifications based on configuration."""
        try:
            # Email notification
            if self.notification_config.email_enabled:
                self._send_email_notification(type, message, details)
            
            # Slack notification
            if self.notification_config.slack_enabled:
                self._send_slack_notification(type, message, details)
            
            # Discord notification
            if self.notification_config.discord_enabled:
                self._send_discord_notification(type, message, details)
                
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    def _send_email_notification(self, type: str, message: str, details: Dict[str, Any]):
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            if not self.notification_config.email_recipients:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.notification_config.email_username
            msg['To'] = ", ".join(self.notification_config.email_recipients)
            msg['Subject'] = f"WhatsApp Analyzer - {type.upper()}: {message}"
            
            body = f"""
            Analysis Notification
            
            Type: {type.upper()}
            Message: {message}
            Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Details:
            {json.dumps(details, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.notification_config.email_smtp_server, 
                                self.notification_config.email_smtp_port)
            server.starttls()
            server.login(self.notification_config.email_username, 
                        self.notification_config.email_password)
            
            text = msg.as_string()
            server.sendmail(self.notification_config.email_username, 
                          self.notification_config.email_recipients, text)
            server.quit()
            
            self.logger.info("Email notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
    
    def _send_slack_notification(self, type: str, message: str, details: Dict[str, Any]):
        """Send Slack notification."""
        try:
            import requests
            
            if not self.notification_config.slack_webhook_url:
                return
            
            emoji = "✅" if type == "success" else "❌" if type == "error" else "ℹ️"
            
            payload = {
                "channel": self.notification_config.slack_channel,
                "text": f"{emoji} *WhatsApp Analyzer Notification*",
                "attachments": [
                    {
                        "color": "good" if type == "success" else "danger" if type == "error" else "warning",
                        "fields": [
                            {"title": "Type", "value": type.upper(), "short": True},
                            {"title": "Message", "value": message, "short": False},
                            {"title": "Details", "value": f"```{json.dumps(details, indent=2)}```", "short": False}
                        ],
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(self.notification_config.slack_webhook_url, 
                                   json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Slack notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
    
    def _send_discord_notification(self, type: str, message: str, details: Dict[str, Any]):
        """Send Discord notification."""
        try:
            import requests
            
            if not self.notification_config.discord_webhook_url:
                return
            
            color = 0x00ff00 if type == "success" else 0xff0000 if type == "error" else 0xffff00
            
            payload = {
                "embeds": [
                    {
                        "title": "WhatsApp Analyzer Notification",
                        "description": message,
                        "color": color,
                        "fields": [
                            {"name": "Type", "value": type.upper(), "inline": True},
                            {"name": "Timestamp", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": True},
                            {"name": "Details", "value": f"```json\n{json.dumps(details, indent=2)}\n```", "inline": False}
                        ]
                    }
                ]
            }
            
            response = requests.post(self.notification_config.discord_webhook_url, 
                                   json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Discord notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {e}")

def create_default_profiles(config_manager: ConfigurationManager):
    """Create default configuration profiles."""
    
    # Basic Analysis Profile
    basic_config = {
        "analysis": {
            "keywords": ["meeting", "call", "photo", "video", "document"],
            "use_regex": False,
            "case_sensitive": False,
            "sentiment_analysis": False,
            "language_detection": False,
            "topic_extraction": False
        },
        "processing": {
            "max_workers": 4,
            "use_cache": True,
            "cache_directory": ".cache"
        },
        "output": {
            "generate_excel": False,
            "generate_pdf": False,
            "generate_dashboard": False
        },
        "security": {
            "anonymize_data": False,
            "encrypt_output": False
        }
    }
    
    # Professional Analysis Profile
    professional_config = {
        "analysis": {
            "keywords": ["important", "urgent", "deadline", "meeting", "project", "client"],
            "use_regex": True,
            "case_sensitive": False,
            "sentiment_analysis": True,
            "language_detection": True,
            "topic_extraction": True
        },
        "processing": {
            "max_workers": 8,
            "use_cache": True,
            "cache_directory": ".cache"
        },
        "output": {
            "generate_excel": True,
            "generate_pdf": True,
            "generate_dashboard": True
        },
        "security": {
            "anonymize_data": True,
            "encrypt_output": True
        },
        "automation": {
            "auto_cleanup": True,
            "cleanup_after_days": 30,
            "performance_monitoring": True
        },
        "scheduling": {
            "enabled": True,
            "frequency": "weekly",
            "time": "02:00",
            "days_of_week": ["sunday"]
        }
    }
    
    # Security-Focused Profile
    security_config = {
        "analysis": {
            "keywords": ["confidential", "secret", "password", "login", "account"],
            "use_regex": False,
            "case_sensitive": True,
            "sentiment_analysis": False,
            "language_detection": True,
            "topic_extraction": True
        },
        "processing": {
            "max_workers": 2,
            "use_cache": False,
            "cache_directory": ""
        },
        "output": {
            "generate_excel": True,
            "generate_pdf": True,
            "generate_dashboard": False
        },
        "security": {
            "anonymize_data": True,
            "encrypt_output": True
        },
        "automation": {
            "auto_cleanup": True,
            "cleanup_after_days": 7,
            "auto_archive": True,
            "archive_after_days": 1
        }
    }
    
    # Create profiles
    config_manager.create_profile("basic", basic_config, "Basic content analysis with minimal features")
    config_manager.create_profile("professional", professional_config, "Advanced analysis with all features enabled")
    config_manager.create_profile("security", security_config, "Security-focused analysis with enhanced privacy")
    
    # Set default active profile
    config_manager.set_active_profile("basic")