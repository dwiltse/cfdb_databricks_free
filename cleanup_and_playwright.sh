#!/bin/bash
# Cleanup low-quality data and setup for Playwright MCP

echo "🧹 Cleaning up low-quality ESPN data"
echo "=" * 40

# Remove low-quality parsed data
if [ -d "cfdb_schedules/2025" ]; then
    echo "📂 Removing low-quality JSON files..."
    rm -rf cfdb_schedules/2025
    echo "   ✅ Removed cfdb_schedules/2025/ (low-quality data)"
else
    echo "   ℹ️  No low-quality JSON data found"
fi

# Keep raw HTML for reference/debugging, but mark it
if [ -d "raw_html/2025" ]; then
    mv raw_html/2025 raw_html/2025_backup_low_quality
    echo "   📦 Moved raw_html/2025 → raw_html/2025_backup_low_quality"
fi

# Create clean directory structure for Playwright results
mkdir -p cfdb_schedules_playwright/2025
echo "   📁 Created cfdb_schedules_playwright/2025/ for high-quality data"

echo ""
echo "📋 Data Status After Cleanup:"
echo "   ❌ cfdb_schedules/2025/ - REMOVED (low-quality)"
echo "   📦 raw_html/2025_backup_low_quality/ - KEPT (for reference)"
echo "   ✅ cfdb_schedules_playwright/2025/ - READY (for Playwright MCP)"

echo ""
echo "🎭 Playwright MCP Setup Instructions:"
echo "1. Ensure Node.js 18+ is installed"
echo "2. Playwright MCP should be available in Claude Code"
echo "3. Use the functions: browser_navigate, browser_snapshot, browser_click"
echo "4. Target URL: https://www.espn.com/college-football/schedule/_/week/1/year/2025/seasontype/2/group/80"