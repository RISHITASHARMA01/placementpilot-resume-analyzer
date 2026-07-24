#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8080}"

cd "$PROJECT_ROOT"
mkdir -p build/classes
javac -d build/classes backend-java/src/main/java/com/placementpilot/ResumeAnalyzerServer.java
java -cp build/classes com.placementpilot.ResumeAnalyzerServer "$PORT"
