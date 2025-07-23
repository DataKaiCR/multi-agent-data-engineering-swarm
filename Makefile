# Multi-Agent Data Engineering Swarm - Development Commands
# Usage: make <command>

.PHONY: help setup run test mcp-start mcp-stop mcp-test mcp-probe clean

# Default target
help:
	@echo "🤖 Multi-Agent Data Engineering Swarm"
	@echo ""
	@echo "Available commands:"
	@echo "  setup        Install dependencies and sync environment"
	@echo "  run          Run the main pipeline application"
	@echo "  test         Run all tests"
	@echo "  mcp-start    Start MCP server in detached mode"
	@echo "  mcp-stop     Stop MCP server"
	@echo "  mcp-test     Test MCP server (starts if needed)"
	@echo "  mcp-probe    Run MCP client probe tests"
	@echo "  mcp-restart  Restart MCP server"
	@echo "  clean        Clean up temporary files and stop processes"
	@echo ""
	@echo "Examples:"
	@echo "  make setup         # First time setup"
	@echo "  make mcp-start     # Start MCP server in background"
	@echo "  make run           # Run main application"
	@echo "  make mcp-probe     # Test MCP tools"

# Setup and installation
setup:
	@echo "📦 Installing dependencies..."
	uv sync
	@echo "✅ Setup complete!"

# Run main application
run:
	@echo "🚀 Running main pipeline..."
	uv run python main.py

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run python -m pytest tests/ -v

# Run specific test files
test-simple:
	@echo "🧪 Running simple tests..."
	uv run python -m pytest tests/test_config.py tests/test_simple.py -v

# Run integration tests
test-integration:
	@echo "🧪 Running integration tests..."
	@if ! pgrep -f "tools/data_tools.py" > /dev/null; then \
		echo "📡 Starting MCP server for integration tests..."; \
		$(MAKE) mcp-start; \
		sleep 3; \
	fi
	uv run python -m pytest tests/ -m integration -v

# Run unit tests only
test-unit:
	@echo "🧪 Running unit tests..."
	uv run python -m pytest tests/ -m "not integration" -v

# MCP Server Management
mcp-start:
	@echo "🔧 Starting MCP server in detached mode..."
	@if pgrep -f "tools/data_tools.py" > /dev/null; then \
		echo "⚠️  MCP server already running (PID: $$(pgrep -f 'tools/data_tools.py'))"; \
	else \
		nohup uv run python tools/data_tools.py > mcp_server.log 2>&1 & \
		echo $$! > mcp_server.pid; \
		sleep 2; \
		if pgrep -f "tools/data_tools.py" > /dev/null; then \
			echo "✅ MCP server started (PID: $$(cat mcp_server.pid))"; \
			echo "📋 Server running on http://127.0.0.1:8000"; \
			echo "📄 Logs: tail -f mcp_server.log"; \
		else \
			echo "❌ Failed to start MCP server"; \
			cat mcp_server.log; \
		fi; \
	fi

mcp-stop:
	@echo "🛑 Stopping MCP server..."
	@if [ -f mcp_server.pid ]; then \
		PID=$$(cat mcp_server.pid); \
		if kill $$PID 2>/dev/null; then \
			echo "✅ MCP server stopped (PID: $$PID)"; \
		else \
			echo "⚠️  Process $$PID not found"; \
		fi; \
		rm -f mcp_server.pid; \
	else \
		pkill -f "tools/data_tools.py" && echo "✅ MCP server stopped" || echo "ℹ️  No MCP server running"; \
	fi

mcp-restart: mcp-stop
	@sleep 1
	@$(MAKE) mcp-start

mcp-status:
	@if pgrep -f "tools/data_tools.py" > /dev/null; then \
		echo "✅ MCP server is running (PID: $$(pgrep -f 'tools/data_tools.py'))"; \
		echo "📋 Server URL: http://127.0.0.1:8000"; \
	else \
		echo "❌ MCP server is not running"; \
	fi

# MCP Testing
mcp-test: 
	@echo "🧪 Testing MCP server..."
	@if ! pgrep -f "tools/data_tools.py" > /dev/null; then \
		echo "📡 Starting MCP server for testing..."; \
		$(MAKE) mcp-start; \
		sleep 3; \
	fi
	@echo "🔍 Running MCP functionality tests..."
	uv run python test_direct.py

mcp-probe:
	@echo "🔍 Running MCP client probe..."
	@if ! pgrep -f "tools/data_tools.py" > /dev/null; then \
		echo "📡 Starting MCP server for probe..."; \
		$(MAKE) mcp-start; \
		sleep 3; \
	fi
	uv run python scripts/mcp_client_probe.py

# Development helpers
dev-logs:
	@if [ -f mcp_server.log ]; then \
		echo "📄 MCP Server logs:"; \
		tail -f mcp_server.log; \
	else \
		echo "❌ No log file found. Is MCP server running?"; \
	fi

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@$(MAKE) mcp-stop
	@rm -f mcp_server.log mcp_server.pid
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Quick development workflow
dev: mcp-start
	@echo "🔄 Development mode activated!"
	@echo "📡 MCP server running in background"
	@echo "🚀 Run 'make run' to test the pipeline"
	@echo "🔍 Run 'make mcp-probe' to test MCP tools"
	@echo "📄 Run 'make dev-logs' to see server logs"

# Show current status
status:
	@echo "📊 Current Status:"
	@$(MAKE) mcp-status
	@echo ""
	@if [ -f mcp_server.log ]; then \
		echo "📄 Recent logs:"; \
		tail -5 mcp_server.log; \
	fi