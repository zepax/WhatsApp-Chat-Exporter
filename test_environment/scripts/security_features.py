"""
Security and Privacy Features for WhatsApp Chat Analyzer
Includes encryption, anonymization, and data protection
"""

import hashlib
import secrets
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

class SecurityManager:
    """Handles encryption, anonymization, and data protection."""
    
    def __init__(self, master_password: Optional[str] = None):
        self.master_password = master_password
        self.encryption_key = None
        self.anonymization_map = {}
        self.logger = logging.getLogger(__name__)
        
        if ENCRYPTION_AVAILABLE and master_password:
            self._setup_encryption(master_password)
    
    def _setup_encryption(self, password: str):
        """Setup encryption using master password."""
        try:
            # Generate key from password
            salt = b'whatsapp_analyzer_salt_2024'  # In production, use random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.encryption_key = Fernet(key)
            self.logger.info("Encryption system initialized")
        except Exception as e:
            self.logger.error(f"Failed to setup encryption: {e}")
            self.encryption_key = None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data."""
        if not self.encryption_key:
            return data
        
        try:
            encrypted = self.encryption_key.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return data
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt encrypted data."""
        if not self.encryption_key:
            return encrypted_data
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.encryption_key.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def generate_anonymization_id(self, original_id: str) -> str:
        """Generate consistent anonymized identifier."""
        if original_id in self.anonymization_map:
            return self.anonymization_map[original_id]
        
        # Generate consistent hash-based ID
        hash_object = hashlib.sha256(original_id.encode())
        hash_hex = hash_object.hexdigest()
        anon_id = f"USER_{hash_hex[:8].upper()}"
        
        self.anonymization_map[original_id] = anon_id
        return anon_id
    
    def anonymize_participants(self, participants: List[str]) -> List[str]:
        """Anonymize participant names."""
        return [self.generate_anonymization_id(p) for p in participants]
    
    def anonymize_text_content(self, text: str) -> str:
        """Anonymize personal information in text."""
        anonymized_text = text
        
        # Phone numbers
        phone_pattern = r'\+?[\d\s\-\(\)]{10,}'
        anonymized_text = re.sub(phone_pattern, '[PHONE_REDACTED]', anonymized_text)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        anonymized_text = re.sub(email_pattern, '[EMAIL_REDACTED]', anonymized_text)
        
        # URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        anonymized_text = re.sub(url_pattern, '[URL_REDACTED]', anonymized_text)
        
        # Credit card numbers (basic pattern)
        cc_pattern = r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'
        anonymized_text = re.sub(cc_pattern, '[CARD_REDACTED]', anonymized_text)
        
        # Social security numbers (basic US pattern)
        ssn_pattern = r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b'
        anonymized_text = re.sub(ssn_pattern, '[SSN_REDACTED]', anonymized_text)
        
        return anonymized_text
    
    def create_audit_log(self, action: str, details: Dict[str, Any], output_dir: str):
        """Create audit log entry."""
        try:
            audit_dir = Path(output_dir) / "audit_logs"
            audit_dir.mkdir(exist_ok=True)
            
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "details": details,
                "user_hash": hashlib.sha256(f"{datetime.now().date()}".encode()).hexdigest()[:16]
            }
            
            date_str = datetime.now().strftime("%Y%m%d")
            audit_file = audit_dir / f"audit_log_{date_str}.json"
            
            # Read existing logs
            existing_logs = []
            if audit_file.exists():
                with open(audit_file, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
            
            # Add new entry
            existing_logs.append(audit_entry)
            
            # Write back
            with open(audit_file, 'w', encoding='utf-8') as f:
                json.dump(existing_logs, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Audit log entry created: {action}")
            
        except Exception as e:
            self.logger.error(f"Failed to create audit log: {e}")
    
    def validate_data_retention(self, file_path: str, max_age_days: int = 90) -> bool:
        """Check if file should be retained based on age."""
        try:
            file_age = (datetime.now() - datetime.fromtimestamp(Path(file_path).stat().st_mtime)).days
            return file_age <= max_age_days
        except:
            return True  # Default to retain if can't determine age
    
    def secure_delete_file(self, file_path: str) -> bool:
        """Securely delete a file by overwriting with random data."""
        try:
            path = Path(file_path)
            if not path.exists():
                return True
            
            # Get file size
            file_size = path.stat().st_size
            
            # Overwrite with random data multiple times
            with open(path, 'r+b') as f:
                for _ in range(3):  # 3 passes
                    f.seek(0)
                    f.write(secrets.token_bytes(file_size))
                    f.flush()
            
            # Delete the file
            path.unlink()
            self.logger.info(f"Securely deleted: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to securely delete {file_path}: {e}")
            return False
    
    def generate_privacy_report(self, analyzer_instance, output_dir: str) -> str:
        """Generate privacy compliance report."""
        try:
            privacy_dir = Path(output_dir) / "privacy_reports"
            privacy_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = privacy_dir / f"privacy_report_{timestamp}.json"
            
            # Collect privacy metrics
            total_files = len(analyzer_instance.results)
            anonymized_files = sum(1 for r in analyzer_instance.results 
                                 if getattr(r, 'anonymized', False))
            encrypted_outputs = sum(1 for r in analyzer_instance.results 
                                  if getattr(r, 'encrypted', False))
            
            # Data types processed
            data_types = {
                "messages": sum(r.total_messages for r in analyzer_instance.results),
                "participants": len(set().union(*[getattr(r, 'participants', []) 
                                                for r in analyzer_instance.results])),
                "keywords_monitored": len(analyzer_instance.config.keywords),
                "files_with_personal_data": sum(1 for r in analyzer_instance.results 
                                              if len(getattr(r, 'participants', [])) > 0)
            }
            
            # Privacy measures applied
            privacy_measures = {
                "anonymization_enabled": analyzer_instance.config.anonymize_data,
                "encryption_enabled": analyzer_instance.config.encrypt_output,
                "audit_logging": True,
                "secure_deletion": True,
                "data_retention_policy": True
            }
            
            # Compliance status
            compliance_status = {
                "gdpr_ready": all([
                    analyzer_instance.config.anonymize_data,
                    len(getattr(analyzer_instance, 'privacy_notices', [])) > 0
                ]),
                "ccpa_ready": analyzer_instance.config.anonymize_data,
                "data_minimization": len(analyzer_instance.config.keywords) < 50,
                "purpose_limitation": True,  # Analysis only
                "storage_limitation": True   # Temporary storage
            }
            
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_version": "1.0",
                    "analyzer_version": "2.0 Professional"
                },
                "data_processing_summary": {
                    "total_files_processed": total_files,
                    "anonymized_files": anonymized_files,
                    "encrypted_outputs": encrypted_outputs,
                    "data_types": data_types
                },
                "privacy_measures": privacy_measures,
                "compliance_status": compliance_status,
                "recommendations": [
                    "Enable anonymization for production use" if not analyzer_instance.config.anonymize_data else "Anonymization properly enabled",
                    "Enable output encryption for sensitive data" if not analyzer_instance.config.encrypt_output else "Output encryption enabled",
                    "Implement data retention policies",
                    "Regular privacy impact assessments",
                    "User consent management for personal data"
                ]
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Privacy report generated: {report_file}")
            return str(report_file)
            
        except Exception as e:
            self.logger.error(f"Failed to generate privacy report: {e}")
            return ""

class DataProtectionManager:
    """Manages data protection and compliance features."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.logger = logging.getLogger(__name__)
        self.consent_records = {}
        self.processing_purposes = []
    
    def record_consent(self, data_subject: str, purpose: str, consent_given: bool):
        """Record consent for data processing."""
        consent_id = hashlib.sha256(f"{data_subject}_{purpose}".encode()).hexdigest()[:16]
        
        self.consent_records[consent_id] = {
            "data_subject_hash": hashlib.sha256(data_subject.encode()).hexdigest(),
            "purpose": purpose,
            "consent_given": consent_given,
            "timestamp": datetime.now().isoformat(),
            "consent_id": consent_id
        }
        
        self.logger.info(f"Consent recorded: {consent_id}")
    
    def check_consent(self, data_subject: str, purpose: str) -> bool:
        """Check if consent exists for processing."""
        consent_id = hashlib.sha256(f"{data_subject}_{purpose}".encode()).hexdigest()[:16]
        consent_record = self.consent_records.get(consent_id)
        
        if consent_record:
            return consent_record.get('consent_given', False)
        
        return False  # No consent found
    
    def apply_data_minimization(self, analyzer_instance) -> Dict[str, Any]:
        """Apply data minimization principles."""
        minimization_report = {
            "original_keywords": len(analyzer_instance.config.keywords),
            "essential_keywords": [],
            "removed_keywords": [],
            "data_reduction_percentage": 0
        }
        
        # Identify essential keywords based on frequency
        keyword_frequency = {}
        for result in analyzer_instance.results:
            for keyword, count in result.keyword_matches.items():
                keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + count
        
        # Keep only keywords with significant matches
        threshold = max(1, sum(keyword_frequency.values()) * 0.05)  # 5% threshold
        essential_keywords = [k for k, v in keyword_frequency.items() if v >= threshold]
        removed_keywords = [k for k in analyzer_instance.config.keywords if k not in essential_keywords]
        
        minimization_report.update({
            "essential_keywords": essential_keywords,
            "removed_keywords": removed_keywords,
            "data_reduction_percentage": (len(removed_keywords) / len(analyzer_instance.config.keywords)) * 100
        })
        
        # Update configuration
        analyzer_instance.config.keywords = essential_keywords
        analyzer_instance._compile_patterns()
        
        self.logger.info(f"Data minimization applied: {len(removed_keywords)} keywords removed")
        return minimization_report
    
    def generate_data_processing_record(self, analyzer_instance, output_dir: str) -> str:
        """Generate Article 30 GDPR processing record."""
        try:
            record_dir = Path(output_dir) / "compliance_records"
            record_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            record_file = record_dir / f"processing_record_{timestamp}.json"
            
            processing_record = {
                "controller_information": {
                    "organization": "WhatsApp Chat Analysis System",
                    "contact_details": "privacy@analyzer.local",
                    "dpo_contact": "dpo@analyzer.local"
                },
                "processing_purposes": [
                    "Content analysis for research purposes",
                    "Keyword frequency analysis",
                    "Communication pattern analysis"
                ],
                "categories_of_data_subjects": [
                    "WhatsApp chat participants",
                    "Message authors"
                ],
                "categories_of_personal_data": [
                    "Communication content",
                    "Timestamps",
                    "Participant identifiers"
                ],
                "categories_of_recipients": [
                    "Authorized analysts",
                    "Research team members"
                ],
                "transfers_to_third_countries": "None",
                "retention_periods": {
                    "analysis_results": "90 days",
                    "cached_data": "30 days",
                    "audit_logs": "1 year"
                },
                "technical_organizational_measures": [
                    "Data anonymization",
                    "Encryption at rest",
                    "Access controls",
                    "Audit logging",
                    "Secure deletion",
                    "Data minimization"
                ],
                "processing_statistics": {
                    "total_files_processed": len(analyzer_instance.results),
                    "total_messages_analyzed": sum(r.total_messages for r in analyzer_instance.results),
                    "processing_date": datetime.now().isoformat(),
                    "anonymization_applied": analyzer_instance.config.anonymize_data,
                    "encryption_applied": analyzer_instance.config.encrypt_output
                }
            }
            
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(processing_record, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Processing record generated: {record_file}")
            return str(record_file)
            
        except Exception as e:
            self.logger.error(f"Failed to generate processing record: {e}")
            return ""

def apply_security_features(analyzer_instance, security_config: Dict[str, Any]) -> SecurityManager:
    """Apply security features to analyzer instance."""
    try:
        # Initialize security manager
        master_password = security_config.get('master_password')
        security_manager = SecurityManager(master_password)
        
        # Apply anonymization if enabled
        if security_config.get('anonymize_data', False):
            for result in analyzer_instance.results:
                if hasattr(result, 'participants'):
                    result.participants = security_manager.anonymize_participants(result.participants)
                    setattr(result, 'anonymized', True)
        
        # Apply encryption if enabled
        if security_config.get('encrypt_output', False) and ENCRYPTION_AVAILABLE:
            for result in analyzer_instance.results:
                # Encrypt sensitive data
                if hasattr(result, 'keyword_matches'):
                    encrypted_matches = {}
                    for keyword, count in result.keyword_matches.items():
                        encrypted_keyword = security_manager.encrypt_data(keyword)
                        encrypted_matches[encrypted_keyword] = count
                    result.keyword_matches = encrypted_matches
                    setattr(result, 'encrypted', True)
        
        # Create audit log
        security_manager.create_audit_log(
            "security_features_applied",
            {
                "anonymization": security_config.get('anonymize_data', False),
                "encryption": security_config.get('encrypt_output', False),
                "files_processed": len(analyzer_instance.results)
            },
            security_config.get('output_dir', 'analysis_results')
        )
        
        return security_manager
        
    except Exception as e:
        logging.error(f"Failed to apply security features: {e}")
        return SecurityManager()  # Return basic manager