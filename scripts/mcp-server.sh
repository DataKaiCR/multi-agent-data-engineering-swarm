#!/bin/bash
# MCP Server Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/mcp_server.pid"
LOG_FILE="$PROJECT_ROOT/mcp_server.log"

cd "$PROJECT_ROOT"

start_server() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "⚠️  MCP server already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    echo "🚀 Starting MCP server..."
    nohup uv run python tools/data_tools.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ MCP server started (PID: $(cat "$PID_FILE"))"
        echo "📋 Server URL: http://127.0.0.1:8000"
        echo "📄 Logs: tail -f $LOG_FILE"
    else
        echo "❌ Failed to start MCP server"
        [ -f "$LOG_FILE" ] && cat "$LOG_FILE"
        return 1
    fi
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill "$PID" 2>/dev/null; then
            echo "✅ MCP server stopped (PID: $PID)"
        else
            echo "⚠️  Process $PID not found"
        fi
        rm -f "$PID_FILE"
    else
        # Fallback: kill by process name
        if pkill -f "tools/data_tools.py" 2>/dev/null; then
            echo "✅ MCP server stopped"
        else
            echo "ℹ️  No MCP server running"
        fi
    fi
}

status_server() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "✅ MCP server is running (PID: $(cat "$PID_FILE"))"
        echo "📋 Server URL: http://127.0.0.1:8000"
    else
        echo "❌ MCP server is not running"
        return 1
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📄 MCP Server logs:"
        tail -f "$LOG_FILE"
    else
        echo "❌ No log file found"
        return 1
    fi
}

probe_server() {
    echo "🔍 Running MCP client probe..."
    if ! status_server >/dev/null 2>&1; then
        echo "📡 Starting MCP server for probe..."
        start_server
        sleep 3
    fi
    uv run python scripts/mcp_client_probe.py
}

case "${1:-}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        status_server
        ;;
    logs)
        show_logs
        ;;
    probe)
        probe_server
        ;;
    *)
        echo "🤖 MCP Server Management"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|probe}"
        echo ""
        echo "Commands:"
        echo "  start    Start MCP server in background"
        echo "  stop     Stop MCP server"
        echo "  restart  Restart MCP server"
        echo "  status   Check if server is running"
        echo "  logs     Show server logs (tail -f)"
        echo "  probe    Test server with client probe"
        echo ""
        echo "Examples:"
        echo "  $0 start        # Start server"
        echo "  $0 probe        # Test server functionality"
        echo "  $0 logs         # Watch logs"
        exit 1
        ;;
esac