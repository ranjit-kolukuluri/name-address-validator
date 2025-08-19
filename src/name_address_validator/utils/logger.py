# src/name_address_validator/utils/logger.py
"""
Enhanced logging utilities for the name and address validator
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import json

class DebugLogger:
    """Enhanced debug logger with performance tracking and categorization"""
    
    def __init__(self):
        self.logs: List[Dict] = []
        self.enabled: bool = True
        self.max_logs: int = 1000
        
    def log(self, level: str, message: str, category: str = "GENERAL", **kwargs):
        """Add a debug log entry with enhanced metadata"""
        if not self.enabled:
            return
            
        log_entry = {
            'timestamp': datetime.now(),
            'level': level.upper(),
            'category': category.upper(), 
            'message': message,
            'details': kwargs
        }
        
        self.logs.append(log_entry)
        
        # Keep only recent logs to prevent memory issues
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Also log to console for server-side monitoring
        timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
        print(f"[{timestamp}] {level.upper()} {category}: {message}")
    
    def info(self, message: str, category: str = "GENERAL", **kwargs):
        """Log info message"""
        self.log("INFO", message, category, **kwargs)
    
    def warning(self, message: str, category: str = "GENERAL", **kwargs):
        """Log warning message"""
        self.log("WARNING", message, category, **kwargs)
    
    def error(self, message: str, category: str = "GENERAL", **kwargs):
        """Log error message"""
        self.log("ERROR", message, category, **kwargs)
    
    def debug(self, message: str, category: str = "GENERAL", **kwargs):
        """Log debug message"""
        self.log("DEBUG", message, category, **kwargs)
    
    def get_logs_by_level(self, level: str) -> List[Dict]:
        """Get all logs of a specific level"""
        return [log for log in self.logs if log['level'] == level.upper()]
    
    def get_logs_by_category(self, category: str) -> List[Dict]:
        """Get all logs of a specific category"""
        return [log for log in self.logs if log['category'] == category.upper()]
    
    def get_recent_logs(self, minutes: int = 5) -> List[Dict]:
        """Get logs from the last N minutes"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [log for log in self.logs if log['timestamp'] > cutoff_time]
    
    def clear(self):
        """Clear all logs"""
        self.logs = []
    
    def export_logs(self, format: str = "json") -> str:
        """Export logs in specified format"""
        if format.lower() == "json":
            return json.dumps(self.logs, default=str, indent=2)
        elif format.lower() == "csv":
            import csv
            import io
            output = io.StringIO()
            if self.logs:
                fieldnames = ['timestamp', 'level', 'category', 'message', 'details']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for log in self.logs:
                    writer.writerow({
                        'timestamp': log['timestamp'].isoformat(),
                        'level': log['level'],
                        'category': log['category'],
                        'message': log['message'],
                        'details': json.dumps(log['details']) if log['details'] else ''
                    })
            return output.getvalue()
        else:
            # Plain text format
            lines = []
            for log in self.logs:
                timestamp = log['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                line = f"[{timestamp}] {log['level']} {log['category']}: {log['message']}"
                if log['details']:
                    line += f" | {json.dumps(log['details'])}"
                lines.append(line)
            return '\n'.join(lines)
    
    def display(self):
        """Display logs in Streamlit interface"""
        if self.logs:
            st.subheader("🔍 Debug Logs")
            
            # Filter controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                level_filter = st.selectbox(
                    "Filter by Level", 
                    options=["ALL"] + list(set(log['level'] for log in self.logs))
                )
            
            with col2:
                category_filter = st.selectbox(
                    "Filter by Category",
                    options=["ALL"] + list(set(log['category'] for log in self.logs))
                )
            
            with col3:
                time_filter = st.selectbox(
                    "Time Range",
                    options=["All Time", "Last 5 min", "Last 15 min", "Last Hour"]
                )
            
            # Apply filters
            filtered_logs = self.logs.copy()
            
            if level_filter != "ALL":
                filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]
            
            if category_filter != "ALL":
                filtered_logs = [log for log in filtered_logs if log['category'] == category_filter]
            
            if time_filter != "All Time":
                minutes_map = {
                    "Last 5 min": 5,
                    "Last 15 min": 15, 
                    "Last Hour": 60
                }
                minutes = minutes_map[time_filter]
                filtered_logs = self.get_recent_logs(minutes)
                if level_filter != "ALL":
                    filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]
                if category_filter != "ALL":
                    filtered_logs = [log for log in filtered_logs if log['category'] == category_filter]
            
            # Display logs
            if filtered_logs:
                log_text = []
                for log in filtered_logs[-50:]:  # Show last 50 logs
                    timestamp = log['timestamp'].strftime("%H:%M:%S.%f")[:-3]
                    details_str = ""
                    if log['details']:
                        details_str = f" | {json.dumps(log['details'], default=str)}"
                    log_line = f"[{timestamp}] {log['level']} {log['category']}: {log['message']}{details_str}"
                    log_text.append(log_line)
                
                st.code("\n".join(log_text), language="text")
                
                # Export options
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Export as JSON"):
                        st.download_button(
                            "Download JSON",
                            data=self.export_logs("json"),
                            file_name=f"debug_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                with col2:
                    if st.button("Export as CSV"):
                        st.download_button(
                            "Download CSV",
                            data=self.export_logs("csv"),
                            file_name=f"debug_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col3:
                    if st.button("Clear Logs"):
                        self.clear()
                        st.success("Logs cleared!")
                        st.experimental_rerun()
            else:
                st.info("No logs found matching the current filters.")
        else:
            st.info("No debug logs available.")


class PerformanceTracker:
    """Performance tracking utility"""
    
    def __init__(self):
        self.metrics: List[Dict] = []
        self.max_metrics: int = 500
    
    def track(self, operation: str, duration_ms: int, success: bool = True, **metadata):
        """Track a performance metric"""
        metric = {
            'timestamp': datetime.now(),
            'operation': operation,
            'duration_ms': duration_ms,
            'success': success,
            'metadata': metadata
        }
        
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_average_duration(self, operation: str) -> Optional[float]:
        """Get average duration for an operation"""
        operation_metrics = [m for m in self.metrics if m['operation'] == operation and m['success']]
        if not operation_metrics:
            return None
        return sum(m['duration_ms'] for m in operation_metrics) / len(operation_metrics)
    
    def get_success_rate(self, operation: str) -> Optional[float]:
        """Get success rate for an operation"""
        operation_metrics = [m for m in self.metrics if m['operation'] == operation]
        if not operation_metrics:
            return None
        successful = sum(1 for m in operation_metrics if m['success'])
        return successful / len(operation_metrics)
    
    def get_recent_metrics(self, minutes: int = 15) -> List[Dict]:
        """Get metrics from the last N minutes"""
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [metric for metric in self.metrics if metric['timestamp'] > cutoff_time]
    
    def clear(self):
        """Clear all metrics"""
        self.metrics = []
    
    def display_summary(self):
        """Display performance summary in Streamlit"""
        if not self.metrics:
            st.info("No performance metrics available.")
            return
        
        st.subheader("📊 Performance Metrics")
        
        # Get unique operations
        operations = list(set(m['operation'] for m in self.metrics))
        
        # Summary table
        summary_data = []
        for operation in operations:
            avg_duration = self.get_average_duration(operation)
            success_rate = self.get_success_rate(operation)
            operation_metrics = [m for m in self.metrics if m['operation'] == operation]
            
            summary_data.append({
                'Operation': operation,
                'Count': len(operation_metrics),
                'Avg Duration (ms)': f"{avg_duration:.1f}" if avg_duration else "N/A",
                'Success Rate': f"{success_rate:.1%}" if success_rate else "N/A"
            })
        
        if summary_data:
            import pandas as pd
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
        
        # Recent metrics
        with st.expander("Recent Metrics (Last 15 minutes)"):
            recent_metrics = self.get_recent_metrics(15)
            if recent_metrics:
                metrics_data = []
                for metric in recent_metrics[-20:]:  # Show last 20
                    metrics_data.append({
                        'Time': metric['timestamp'].strftime("%H:%M:%S"),
                        'Operation': metric['operation'],
                        'Duration (ms)': metric['duration_ms'],
                        'Success': "✅" if metric['success'] else "❌"
                    })
                
                import pandas as pd
                df = pd.DataFrame(metrics_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No recent metrics available.")


# Global instances for easy import
debug_logger = DebugLogger()
performance_tracker = PerformanceTracker()