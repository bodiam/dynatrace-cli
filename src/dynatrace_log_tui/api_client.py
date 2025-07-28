"""
Dynatrace API client for executing DQL queries
"""
import os
import requests
from datetime import datetime
from typing import Dict, Any, List

from .models import TimeRange


class DynatraceClient:
    """Client for interacting with Dynatrace API"""
    
    def __init__(self):
        self.base_url, self.token = self._get_config()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })
    
    def _get_config(self) -> tuple[str, str]:
        """Get the Dynatrace configuration from environment variables"""
        base_url = os.getenv("DYNATRACE_BASE_URL")
        token = os.getenv("DYNATRACE_TOKEN")
        
        missing_vars = []
        if not base_url:
            missing_vars.append("DYNATRACE_BASE_URL")
        if not token:
            missing_vars.append("DYNATRACE_TOKEN")
        
        if missing_vars:
            error_msg = "Required environment variables are not set:\n"
            for var in missing_vars:
                if var == "DYNATRACE_BASE_URL":
                    error_msg += f"  • {var}: Your Dynatrace environment URL (e.g., https://abc12345.apps.dynatrace.com)\n"
                elif var == "DYNATRACE_TOKEN":
                    error_msg += f"  • {var}: Your Dynatrace API token\n"
            
            error_msg += "\nTo set up your environment:\n"
            error_msg += "1. Find your Dynatrace environment URL in your Dynatrace web UI\n"
            error_msg += "2. Create an API token at: https://myaccount.dynatrace.com/platformTokens\n"
            error_msg += "   Required scopes: storage:logs:read, storage:metrics:read\n"
            error_msg += "3. Set the environment variables:\n"
            error_msg += "   export DYNATRACE_BASE_URL='https://your-env.apps.dynatrace.com'\n"
            error_msg += "   export DYNATRACE_TOKEN='dt0s16.YOUR_TOKEN_HERE'\n"
            
            raise ValueError(error_msg)
        
        # Ensure base URL doesn't end with slash
        base_url = base_url.rstrip('/')
        
        return base_url, token
    
    def execute_query(self, query: str, time_range: str = "30m", max_records: int = 1000) -> Dict[str, Any]:
        """Execute a DQL query against Dynatrace"""
        try:
            start_time, end_time = TimeRange.calculate_timeframe(time_range)
            
            payload = {
                "query": query,
                "defaultTimeframeStart": start_time,
                "defaultTimeframeEnd": end_time,
                "maxResultRecords": max_records,
                "requestTimeoutMilliseconds": 30000
            }
            
            url = f"{self.base_url}/platform/storage/query/v1/query:execute"
            response = self.session.post(url, json=payload, timeout=35)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return {"error": error_msg}
                
        except requests.exceptions.Timeout:
            return {"error": "Request timeout - query took too long to execute"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error - unable to reach Dynatrace API"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def convert_to_log_format(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert Dynatrace API response to internal log format"""
        if "error" in api_response:
            return []
        
        logs = []
        try:
            # Handle the Dynatrace API response structure
            if "result" in api_response and "records" in api_response["result"]:
                records = api_response["result"]["records"]
                
                for record in records:
                    # Map Dynatrace log fields to internal format
                    log_entry = {
                        "timestamp": datetime.fromisoformat(record.get("timestamp", datetime.now().isoformat()).replace("Z", "+00:00")),
                        "level": record.get("loglevel", "INFO").upper(),
                        "service": record.get("dt.entity.service", record.get("service_name", "unknown")),
                        "message": record.get("content", record.get("message", "")),
                        "host": record.get("dt.entity.host", record.get("host", "unknown")),
                        "trace_id": record.get("trace_id", ""),
                        "span_id": record.get("span_id", ""),
                        "content": record.get("content", record.get("message", ""))
                    }
                    logs.append(log_entry)
                    
        except Exception as e:
            # Return empty list if parsing fails
            pass
            
        return logs