from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

DUMMY_LOGS = [
    {
        "timestamp": datetime.now() - timedelta(minutes=1),
        "level": "ERROR",
        "service": "payment-service",
        "message": "Failed to process payment for order #12345",
        "trace_id": "abc123def456",
        "span_id": "789xyz",
        "host": "prod-server-01",
        "content": "Payment processing failed due to insufficient funds"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=2),
        "level": "INFO",
        "service": "user-service",
        "message": "User authentication successful",
        "trace_id": "def456ghi789",
        "span_id": "123abc",
        "host": "prod-server-02",
        "content": "User john.doe@example.com logged in successfully"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=3),
        "level": "WARN",
        "service": "inventory-service",
        "message": "Low stock alert for product SKU-001",
        "trace_id": "ghi789jkl012",
        "span_id": "456def",
        "host": "prod-server-03",
        "content": "Product SKU-001 has only 5 items remaining in inventory"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=5),
        "level": "ERROR",
        "service": "database-service",
        "message": "Database connection timeout",
        "trace_id": "jkl012mno345",
        "span_id": "789ghi",
        "host": "db-server-01",
        "content": "Connection to primary database timed out after 30 seconds"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=7),
        "level": "INFO",
        "service": "api-gateway",
        "message": "Health check passed",
        "trace_id": "mno345pqr678",
        "span_id": "012jkl",
        "host": "gateway-01",
        "content": "All services responding normally"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=10),
        "level": "DEBUG",
        "service": "cache-service",
        "message": "Cache miss for key user:12345",
        "trace_id": "pqr678stu901",
        "span_id": "345mno",
        "host": "cache-server-01",
        "content": "Key user:12345 not found in Redis cache, fetching from database"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=12),
        "level": "ERROR",
        "service": "notification-service",
        "message": "Failed to send email notification",
        "trace_id": "stu901vwx234",
        "span_id": "678pqr",
        "host": "notification-01",
        "content": "SMTP server connection failed: Connection refused"
    },
    {
        "timestamp": datetime.now() - timedelta(minutes=15),
        "level": "INFO",
        "service": "order-service",
        "message": "New order created successfully",
        "trace_id": "vwx234yza567",
        "span_id": "901stu",
        "host": "order-server-01",
        "content": "Order #12346 created for customer ID 7890"
    },
]

def generate_more_logs(count: int = 100) -> List[Dict[str, Any]]:
    services = ["payment-service", "user-service", "inventory-service", "database-service", 
                "api-gateway", "cache-service", "notification-service", "order-service",
                "auth-service", "analytics-service", "recommendation-service"]
    levels = ["ERROR", "WARN", "INFO", "DEBUG"]
    hosts = ["prod-server-01", "prod-server-02", "prod-server-03", "db-server-01", 
             "gateway-01", "cache-server-01", "notification-01", "order-server-01"]
    
    logs = []
    for i in range(count):
        log = {
            "timestamp": datetime.now() - timedelta(minutes=random.randint(1, 1440)),
            "level": random.choice(levels),
            "service": random.choice(services),
            "message": f"Log message #{i+1} from {random.choice(services)}",
            "trace_id": f"trace_{random.randint(100000, 999999)}",
            "span_id": f"span_{random.randint(100, 999)}",
            "host": random.choice(hosts),
            "content": f"Detailed log content for message #{i+1} with additional context"
        }
        logs.append(log)
    
    return DUMMY_LOGS + logs

def filter_logs(logs: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    if not query.strip():
        return logs
    
    query_lower = query.lower()
    filtered = []
    
    for log in logs:
        if (query_lower in log["message"].lower() or 
            query_lower in log["service"].lower() or
            query_lower in log["level"].lower() or
            query_lower in log["content"].lower()):
            filtered.append(log)
    
    return filtered