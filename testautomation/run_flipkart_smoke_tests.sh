#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

mkdir -p Output/Screenshots Testsuite

robot \
  --outputdir Testsuite \
  --log smoke_log.html \
  --report smoke_report.html \
  --output smoke_output.xml \
  --include smoke \
  --variable rbt_env:qa \
  --variable rbt_usr:Default \
  Testsuite/FlipkartSmokeTestSuite.robot
