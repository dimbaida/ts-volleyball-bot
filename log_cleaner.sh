file=".log"
line_count=$(wc -l < "$file")
threshold=1000

if [ "$line_count" -gt "$threshold" ]; then
    lines_to_delete=$((line_count - threshold))
    sed -i "1,${lines_to_delete}d" "$file"
fi

