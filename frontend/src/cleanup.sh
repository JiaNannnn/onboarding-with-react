#!/bin/bash
# Script to clean up unused pages and components

# Remove unused pages
rm -rf src/pages/Dashboard
rm -rf src/pages/FetchPoints
rm -rf src/pages/GroupPoints
rm -rf src/pages/MapPoints
rm -rf src/pages/SavedMappings
rm -rf src/pages/Login

# Create a README.md in the pages directory to explain the cleanup
cat > src/pages/README.md << 'EOF'
# Pages Structure

This directory has been simplified to only include:

- **DevTools/ApiAnalytics**: Dashboard for monitoring deprecated API usage
- **DevTools/MigrationAssistant**: Tool for automated code refactoring

All other pages have been removed as part of the API client architecture migration.
EOF

# Simplify components for migration tools
echo "Maintaining only essential components..."