#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

mkdir -p Output/Screenshots Testsuite

robot \
  --outputdir Testsuite \
  --log regression_log.html \
  --report regression_report.html \
  --output regression_output.xml \
  --include regression \
  --variable rbt_env:qa \
  --variable rbt_usr:Default \
  Testsuite/FlipkartRegressionTestSuite.robot
