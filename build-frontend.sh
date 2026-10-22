#!/bin/bash
# Build Vue.js frontend and output to app/static/dist
cd "$(dirname "$0")/frontend"
npm install
npx vite build
echo "✅ Frontend built → app/static/dist/"
