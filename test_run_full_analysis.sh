#!/bin/bash
# Test script for run_full_analysis.sh modifications

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to print test results
print_test_result() {
    local test_name="$1"
    local result="$2"
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Clean up function
cleanup() {
    rm -f .analysis_progress
    rm -f v3_full_*.log
}

echo "========================================================================"
echo "Testing run_full_analysis.sh modifications"
echo "========================================================================"
echo ""

# Test 1: Invalid batch number (non-numeric)
echo "Test 1: Invalid batch number (non-numeric)"
if ./run_full_analysis.sh abc 2>&1 | grep -q "Error: Batch number must be a positive integer"; then
    print_test_result "Invalid batch number (non-numeric)" "PASS"
else
    print_test_result "Invalid batch number (non-numeric)" "FAIL"
fi
echo ""

# Test 2: Invalid batch number (too low)
echo "Test 2: Invalid batch number (too low)"
if ./run_full_analysis.sh 0 2>&1 | grep -q "Error: Batch number must be between 1 and 10"; then
    print_test_result "Invalid batch number (too low)" "PASS"
else
    print_test_result "Invalid batch number (too low)" "FAIL"
fi
echo ""

# Test 3: Invalid batch number (too high)
echo "Test 3: Invalid batch number (too high)"
if ./run_full_analysis.sh 11 2>&1 | grep -q "Error: Batch number must be between 1 and 10"; then
    print_test_result "Invalid batch number (too high)" "PASS"
else
    print_test_result "Invalid batch number (too high)" "FAIL"
fi
echo ""

# Test 4: Valid batch number with resume message
echo "Test 4: Valid batch number with resume message"
cleanup
# Create a mock Python script that exits immediately for testing
cat > /tmp/mock_analysis.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.exit(0)
EOF
chmod +x /tmp/mock_analysis.py

# Temporarily replace the python3 command with our mock for this test
# We'll just check if the script accepts the batch number
if timeout 5 ./run_full_analysis.sh 5 2>&1 | grep -q "Resuming from batch 5"; then
    print_test_result "Valid batch number with resume message" "PASS"
else
    print_test_result "Valid batch number with resume message" "FAIL"
fi
cleanup
echo ""

# Test 5: Script structure validation
echo "Test 5: Script structure validation"
SCRIPT_VALID=true

# Check for set -o pipefail
if ! grep -q "set -o pipefail" run_full_analysis.sh; then
    echo "  - Missing 'set -o pipefail' to catch pipe failures"
    SCRIPT_VALID=false
fi

# Check for START_BATCH variable
if ! grep -q "START_BATCH=1" run_full_analysis.sh; then
    echo "  - Missing START_BATCH initialization"
    SCRIPT_VALID=false
fi

# Check for PROGRESS_FILE variable
if ! grep -q 'PROGRESS_FILE=".analysis_progress"' run_full_analysis.sh; then
    echo "  - Missing PROGRESS_FILE variable"
    SCRIPT_VALID=false
fi

# Check for TOTAL_INSTANCES variable
if ! grep -q "TOTAL_INSTANCES=500" run_full_analysis.sh; then
    echo "  - Missing TOTAL_INSTANCES variable"
    SCRIPT_VALID=false
fi

# Check for command line argument parsing
if ! grep -q 'if \[ \$# -gt 0 \]' run_full_analysis.sh; then
    echo "  - Missing command line argument parsing"
    SCRIPT_VALID=false
fi

# Check for batch number validation
if ! grep -q "Error: Batch number must be between 1 and" run_full_analysis.sh; then
    echo "  - Missing batch number validation"
    SCRIPT_VALID=false
fi

# Check for progress file saving on success
if ! grep -q 'echo "\$BATCH_NUM" > "\$PROGRESS_FILE"' run_full_analysis.sh; then
    echo "  - Missing progress file save on success"
    SCRIPT_VALID=false
fi

# Check for stopping execution on failure
if ! grep -q "STOPPING EXECUTION" run_full_analysis.sh; then
    echo "  - Missing stop execution on failure"
    SCRIPT_VALID=false
fi

# Check for progress summary on failure
if ! grep -q "Progress Summary:" run_full_analysis.sh; then
    echo "  - Missing progress summary on failure"
    SCRIPT_VALID=false
fi

# Check for resume command on failure
if ! grep -q "To resume after fixing the issue:" run_full_analysis.sh; then
    echo "  - Missing resume command on failure"
    SCRIPT_VALID=false
fi

# Check for success message
if ! grep -q "ALL BATCHES COMPLETED SUCCESSFULLY" run_full_analysis.sh; then
    echo "  - Missing success message"
    SCRIPT_VALID=false
fi

# Check for progress file cleanup on completion
if ! grep -q 'rm "\$PROGRESS_FILE"' run_full_analysis.sh; then
    echo "  - Missing progress file cleanup on completion"
    SCRIPT_VALID=false
fi

# Check that "Continue to next batch" is removed
if grep -q "Continuing to next batch" run_full_analysis.sh; then
    echo "  - Found old 'Continue to next batch' logic (should be removed)"
    SCRIPT_VALID=false
fi

# Check that FAILED_BATCHES array is removed
if grep -q "FAILED_BATCHES=()" run_full_analysis.sh; then
    echo "  - Found old FAILED_BATCHES array (should be removed)"
    SCRIPT_VALID=false
fi

# Check for correct loop start
if ! grep -q 'seq \$((START_BATCH - 1))' run_full_analysis.sh; then
    echo "  - Loop does not start from START_BATCH"
    SCRIPT_VALID=false
fi

if [ "$SCRIPT_VALID" = true ]; then
    print_test_result "Script structure validation" "PASS"
else
    print_test_result "Script structure validation" "FAIL"
fi
echo ""

# Test 6: Check progress summary format
echo "Test 6: Progress summary format on failure"
FORMAT_VALID=true

# Check for emoji and formatting in progress summary
if ! grep -q "📊 Progress Summary:" run_full_analysis.sh; then
    echo "  - Missing progress summary emoji"
    FORMAT_VALID=false
fi

if ! grep -q "✅ Successfully completed batches:" run_full_analysis.sh; then
    echo "  - Missing completed batches line"
    FORMAT_VALID=false
fi

if ! grep -q "✅ Successfully completed instances:" run_full_analysis.sh; then
    echo "  - Missing completed instances line"
    FORMAT_VALID=false
fi

if ! grep -q "❌ Failed at batch:" run_full_analysis.sh; then
    echo "  - Missing failed batch line"
    FORMAT_VALID=false
fi

if ! grep -q "📌 Remaining batches:" run_full_analysis.sh; then
    echo "  - Missing remaining batches line"
    FORMAT_VALID=false
fi

if ! grep -q "📌 Remaining instances:" run_full_analysis.sh; then
    echo "  - Missing remaining instances line"
    FORMAT_VALID=false
fi

if ! grep -q "🔧 To resume after fixing the issue:" run_full_analysis.sh; then
    echo "  - Missing resume instruction"
    FORMAT_VALID=false
fi

if [ "$FORMAT_VALID" = true ]; then
    print_test_result "Progress summary format on failure" "PASS"
else
    print_test_result "Progress summary format on failure" "FAIL"
fi
echo ""

# Test 7: Check success message format
echo "Test 7: Success message format"
SUCCESS_FORMAT_VALID=true

if ! grep -q "🎉 ALL BATCHES COMPLETED SUCCESSFULLY!" run_full_analysis.sh; then
    echo "  - Missing celebration emoji in success message"
    SUCCESS_FORMAT_VALID=false
fi

if ! grep -q "Total batches processed:" run_full_analysis.sh; then
    echo "  - Missing total batches in success message"
    SUCCESS_FORMAT_VALID=false
fi

if ! grep -q "Total instances processed:" run_full_analysis.sh; then
    echo "  - Missing total instances in success message"
    SUCCESS_FORMAT_VALID=false
fi

if ! grep -q "📁 Results location:" run_full_analysis.sh; then
    echo "  - Missing results location in success message"
    SUCCESS_FORMAT_VALID=false
fi

if ! grep -q "📝 Log file:" run_full_analysis.sh; then
    echo "  - Missing log file in success message"
    SUCCESS_FORMAT_VALID=false
fi

if [ "$SUCCESS_FORMAT_VALID" = true ]; then
    print_test_result "Success message format" "PASS"
else
    print_test_result "Success message format" "FAIL"
fi
echo ""

# Cleanup
cleanup
rm -f /tmp/mock_analysis.py

# Summary
echo "========================================================================"
echo "Test Summary"
echo "========================================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "========================================================================"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
