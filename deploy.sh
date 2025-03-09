#!/bin/bash

# Run article collection script
python3 collect_articles.py

# Build Hugo site
hugo --minify -d ../docs

# Commit and push changes
git add -A .
git commit -m "Auto-update: $(date +'%Y-%m-%d %H:%M:%S')"
git push origin main