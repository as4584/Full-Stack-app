"""
Security monitoring and alerting system
Real-time threat detection and logging
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SecurityMonitor:
    """Real-time security monitoring"""

    def __init__(self):
        self.failed_attempts: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.suspicious_activity: List[Dict[str, Any]] = []

    async def log_failed_attempt(self, ip: str, endpoint: str, reason: str):
        """Log failed authentication/access attempt"""
        now = time.time()

        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = []

        self.failed_attempts[ip].append(now)

        # Clean old attempts (older than 1 hour)
        cutoff = now - 3600
        self.failed_attempts[ip] = [
            attempt for attempt in self.failed_attempts[ip] if attempt > cutoff
        ]

        # Block IP if too many failed attempts
        if len(self.failed_attempts[ip]) >= 5:
            self.blocked_ips[ip] = now + 3600  # Block for 1 hour
            logger.warning(
                "IP blocked due to repeated failed attempts",
                ip=ip,
                endpoint=endpoint,
                reason=reason,
                attempts=len(self.failed_attempts[ip]),
            )

            # Alert security team
            await self._send_security_alert(
                f"IP {ip} blocked - {len(self.failed_attempts[ip])} failed attempts",
                {"ip": ip, "endpoint": endpoint, "reason": reason},
            )

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip not in self.blocked_ips:
            return False

        # Check if block has expired
        if time.time() > self.blocked_ips[ip]:
            del self.blocked_ips[ip]
            return False

        return True

    async def log_suspicious_activity(
        self, activity_type: str, details: Dict[str, Any]
    ):
        """Log suspicious activity for analysis"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": activity_type,
            "details": details,
        }

        self.suspicious_activity.append(event)

        # Keep only last 1000 events
        if len(self.suspicious_activity) > 1000:
            self.suspicious_activity = self.suspicious_activity[-1000:]

        logger.warning("Suspicious activity detected", **event)

        # Check for patterns that require immediate action
        if self._is_critical_threat(activity_type, details):
            await self._send_security_alert(
                f"Critical threat detected: {activity_type}", details
            )

    def _is_critical_threat(self, activity_type: str, details: Dict[str, Any]) -> bool:
        """Determine if activity represents critical threat"""
        critical_patterns = [
            "sql_injection_attempt",
            "xss_attempt",
            "directory_traversal",
            "command_injection",
            "authentication_bypass",
        ]

        return activity_type in critical_patterns

    async def _send_security_alert(self, message: str, details: Dict[str, Any]):
        """Send security alert (implement your preferred alerting method)"""
        # This would integrate with your alerting system
        # Examples: email, Slack, PagerDuty, etc.
        logger.critical("SECURITY ALERT", message=message, details=details)

        # You could implement email alerts here:
        # await send_email_alert(message, details)

    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate security status report"""
        now = time.time()
        hour_ago = now - 3600

        recent_attempts = sum(
            len([attempt for attempt in attempts if attempt > hour_ago])
            for attempts in self.failed_attempts.values()
        )

        blocked_count = len(self.blocked_ips)

        recent_suspicious = [
            event
            for event in self.suspicious_activity
            if datetime.fromisoformat(event["timestamp"])
            > datetime.utcnow() - timedelta(hours=1)
        ]

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "failed_attempts_last_hour": recent_attempts,
            "currently_blocked_ips": blocked_count,
            "suspicious_activities_last_hour": len(recent_suspicious),
            "top_threat_types": self._get_top_threat_types(recent_suspicious),
        }

    def _get_top_threat_types(self, activities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get most common threat types"""
        threat_counts = {}
        for activity in activities:
            threat_type = activity.get("type", "unknown")
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1

        # Sort by count and return top 5
        return dict(sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:5])


# Global monitor instance
security_monitor = SecurityMonitor()
