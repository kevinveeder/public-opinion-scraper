"""Alert management and notification system."""

import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from ..storage.database import get_db
from ..storage.models import Alert, Keyword
from ..utils.config import get_config, get_secrets
from ..analysis.analytics import get_analytics

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.db = get_db()
        self.config = get_config()
        self.secrets = get_secrets()
        self.analytics = get_analytics()
    
    def check_and_create_alerts(self, keyword: str) -> List[Alert]:
        """Check alert conditions and create alerts if necessary."""
        created_alerts = []
        
        try:
            # Get alert conditions from analytics
            alert_conditions = self.analytics.check_alert_conditions(keyword)
            
            # Get keyword object
            with self.db.get_session() as session:
                keyword_obj = session.query(Keyword).filter_by(keyword=keyword).first()
                if not keyword_obj:
                    logger.warning(f"Keyword '{keyword}' not found")
                    return created_alerts
                
                keyword_id = keyword_obj.id
            
            for condition in alert_conditions:
                if condition.triggered:
                    # Check if similar alert already exists recently
                    if not self._alert_exists_recently(keyword_id, condition.alert_type, hours=1):
                        alert_data = {
                            'keyword_id': keyword_id,
                            'alert_type': condition.alert_type,
                            'severity': condition.severity,
                            'message': condition.message,
                            'current_value': condition.current_value,
                            'threshold_value': condition.threshold_value,
                            'metadata': {
                                'keyword': keyword,
                                'detection_time': datetime.utcnow().isoformat()
                            }
                        }
                        
                        alert = self.db.add_alert(alert_data)
                        created_alerts.append(alert)
                        
                        logger.info(f"Created alert for {keyword}: {condition.message}")
                        
                        # Send notifications if enabled
                        self._send_notifications(alert)
            
            return created_alerts
            
        except Exception as e:
            logger.error(f"Error checking alerts for {keyword}: {e}")
            return created_alerts
    
    def _alert_exists_recently(self, keyword_id: int, alert_type: str, hours: int = 1) -> bool:
        """Check if similar alert exists recently to avoid spam."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with self.db.get_session() as session:
                existing_alert = session.query(Alert).filter(
                    Alert.keyword_id == keyword_id,
                    Alert.alert_type == alert_type,
                    Alert.created_at >= cutoff_time,
                    Alert.is_active == True
                ).first()
                
                return existing_alert is not None
                
        except Exception as e:
            logger.error(f"Error checking existing alerts: {e}")
            return False
    
    def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert."""
        try:
            # Email notifications
            if self._email_enabled():
                self._send_email_notification(alert)
            
            # Slack notifications
            if self._slack_enabled():
                self._send_slack_notification(alert)
            
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
    
    def _email_enabled(self) -> bool:
        """Check if email notifications are enabled."""
        email_config = self.secrets.get('email', {})
        return bool(email_config.get('email') and email_config.get('password'))
    
    def _slack_enabled(self) -> bool:
        """Check if Slack notifications are enabled."""
        slack_config = self.secrets.get('slack', {})
        return bool(slack_config.get('webhook_url'))
    
    def _send_email_notification(self, alert: Alert) -> None:
        """Send email notification for alert."""
        try:
            email_config = self.secrets.get('email', {})
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = email_config['email']
            msg['To'] = email_config['email']  # Send to self for now
            msg['Subject'] = f"[Sentiment Monitor] {alert.severity.upper()} Alert - {alert.keyword_rel.keyword}"
            
            # Email body
            body = f"""
Sentiment Monitor Alert

Keyword: {alert.keyword_rel.keyword}
Alert Type: {alert.alert_type}
Severity: {alert.severity}
Message: {alert.message}

Current Value: {alert.current_value}
Threshold: {alert.threshold_value}
Time: {alert.created_at}

---
Sentiment Monitor by Kevin Veeder
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(
                email_config.get('smtp_server', 'smtp.gmail.com'),
                email_config.get('smtp_port', 587)
            )
            server.starttls()
            server.login(email_config['email'], email_config['password'])
            
            text = msg.as_string()
            server.sendmail(email_config['email'], email_config['email'], text)
            server.quit()
            
            logger.info(f"Email notification sent for alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _send_slack_notification(self, alert: Alert) -> None:
        """Send Slack notification for alert."""
        try:
            slack_config = self.secrets.get('slack', {})
            webhook_url = slack_config['webhook_url']
            
            # Determine prefix based on severity
            severity_prefix = {
                'critical': '[CRITICAL]',
                'high': '[HIGH]',
                'medium': '[MEDIUM]',
                'low': '[INFO]'
            }
            prefix = severity_prefix.get(alert.severity, '[ALERT]')
            
            # Color based on severity
            color_map = {
                'critical': '#FF0000',
                'high': '#FF6B35',
                'medium': '#F7931E',
                'low': '#36A64F'
            }
            color = color_map.get(alert.severity, '#F7931E')
            
            # Create Slack message
            slack_data = {
                'text': f'{prefix} Sentiment Alert - {alert.keyword_rel.keyword}',
                'attachments': [
                    {
                        'color': color,
                        'fields': [
                            {
                                'title': 'Keyword',
                                'value': alert.keyword_rel.keyword,
                                'short': True
                            },
                            {
                                'title': 'Severity',
                                'value': alert.severity.upper(),
                                'short': True
                            },
                            {
                                'title': 'Alert Type',
                                'value': alert.alert_type.replace('_', ' ').title(),
                                'short': True
                            },
                            {
                                'title': 'Current Value',
                                'value': f'{alert.current_value:.3f}',
                                'short': True
                            },
                            {
                                'title': 'Message',
                                'value': alert.message,
                                'short': False
                            }
                        ],
                        'footer': 'Sentiment Monitor',
                        'ts': int(alert.created_at.timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=slack_data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent for alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def get_active_alerts(self, keyword: Optional[str] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by keyword."""
        try:
            with self.db.get_session() as session:
                query = session.query(Alert).filter(
                    Alert.is_active == True,
                    Alert.is_acknowledged == False
                )
                
                if keyword:
                    keyword_obj = session.query(Keyword).filter_by(keyword=keyword).first()
                    if keyword_obj:
                        query = query.filter(Alert.keyword_id == keyword_obj.id)
                
                return query.order_by(Alert.created_at.desc()).all()
                
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def acknowledge_alert(self, alert_id: int) -> bool:
        """Acknowledge an alert."""
        try:
            with self.db.get_session() as session:
                alert = session.get(Alert, alert_id)
                if alert:
                    alert.is_acknowledged = True
                    alert.acknowledged_at = datetime.utcnow()
                    session.commit()
                    logger.info(f"Alert {alert_id} acknowledged")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert."""
        try:
            with self.db.get_session() as session:
                alert = session.get(Alert, alert_id)
                if alert:
                    alert.is_active = False
                    alert.resolved_at = datetime.utcnow()
                    session.commit()
                    logger.info(f"Alert {alert_id} resolved")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
    
    def cleanup_old_alerts(self, days: int = 30) -> int:
        """Clean up old resolved alerts."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with self.db.get_session() as session:
                old_alerts = session.query(Alert).filter(
                    Alert.is_active == False,
                    Alert.resolved_at < cutoff_date
                )
                
                count = old_alerts.count()
                old_alerts.delete()
                session.commit()
                
                logger.info(f"Cleaned up {count} old alerts")
                return count
                
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")
            return 0
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alert statistics."""
        try:
            with self.db.get_session() as session:
                # Count alerts by severity
                severity_counts = {}
                for severity in ['critical', 'high', 'medium', 'low']:
                    count = session.query(Alert).filter(
                        Alert.severity == severity,
                        Alert.is_active == True
                    ).count()
                    severity_counts[severity] = count
                
                # Count alerts by type
                type_counts = {}
                alert_types = session.query(Alert.alert_type).distinct().all()
                for (alert_type,) in alert_types:
                    count = session.query(Alert).filter(
                        Alert.alert_type == alert_type,
                        Alert.is_active == True
                    ).count()
                    type_counts[alert_type] = count
                
                # Recent activity
                last_24h = datetime.utcnow() - timedelta(hours=24)
                recent_count = session.query(Alert).filter(
                    Alert.created_at >= last_24h
                ).count()
                
                return {
                    'total_active': sum(severity_counts.values()),
                    'by_severity': severity_counts,
                    'by_type': type_counts,
                    'recent_24h': recent_count,
                    'generated_at': datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"Error getting alert summary: {e}")
            return {}


# Global alert manager instance
alert_manager = AlertManager()

def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    return alert_manager