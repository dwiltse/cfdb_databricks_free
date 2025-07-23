#!/bin/bash
# ESPN 2025 Schedule Downloader
# Downloads raw HTML for all weeks of 2025 college football season

echo "🏈 ESPN 2025 Schedule Downloader"
echo "================================"

# Create output directory
mkdir -p raw_html/2025
echo "📁 Created directory: raw_html/2025"

# Download each week
for week in {1..15}; do
    url="https://www.espn.com/college-football/schedule/_/week/$week/year/2025/seasontype/2/group/80"
    output="raw_html/2025/week_$week.html"
    
    echo "📥 Downloading Week $week..."
    
    # Download with proper headers and error handling
    curl -H "User-Agent: Mozilla/5.0 (compatible; CFDB-Scraper/1.0)" \
         -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
         -H "Accept-Language: en-US,en;q=0.5" \
         -H "Accept-Encoding: gzip, deflate" \
         -H "Connection: keep-alive" \
         --retry 3 \
         --retry-delay 2 \
         --max-time 30 \
         --compressed \
         -s "$url" > "$output"
    
    # Check if download was successful
    if [ -s "$output" ]; then
        file_size=$(wc -c < "$output")
        echo "   ✅ Week $week downloaded ($file_size bytes)"
        
        # Quick validation - check if it contains schedule data
        if grep -q "schedule" "$output" && grep -q "game" "$output"; then
            echo "   ✅ Contains schedule data"
        else
            echo "   ⚠️  May not contain schedule data (check manually)"
        fi
    else
        echo "   ❌ Week $week failed - empty file"
        rm -f "$output"  # Remove empty file
    fi
    
    # Be respectful to ESPN servers
    echo "   ⏱️  Waiting 3 seconds..."
    sleep 3
done

echo ""
echo "📊 Download Summary:"
echo "==================="

total_files=0
total_size=0

for week in {1..15}; do
    file="raw_html/2025/week_$week.html"
    if [ -f "$file" ]; then
        size=$(wc -c < "$file")
        total_files=$((total_files + 1))
        total_size=$((total_size + size))
        echo "Week $week: $(numfmt --to=iec $size)"
    else
        echo "Week $week: MISSING"
    fi
done

echo ""
echo "📈 Total files: $total_files/15"
echo "📈 Total size: $(numfmt --to=iec $total_size)"

if [ $total_files -eq 15 ]; then
    echo "🎉 All weeks downloaded successfully!"
    echo "🔄 Next step: Run 'python3 parse_espn_html.py' to extract JSON data"
else
    echo "⚠️  Some weeks failed to download. Check manually and re-run if needed."
fi