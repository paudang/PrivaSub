import os
import sys
import unittest
import io

def main():
    # Force UTF-8 encoding on Windows terminal output
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    print("====================================================")
    print("           PrivaSub Automated Unit Tests            ")
    print("====================================================\n")

    # Resolve tests directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(project_dir, "tests")

    # Discover and load tests from the tests directory
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_dir, pattern="test_*.py")

    # Filter out integration tests if --exclude-integration is specified
    if "--exclude-integration" in sys.argv:
        print("[Tests] Excluding integration tests from the run...")
        filtered_suite = unittest.TestSuite()
        def filter_tests(suite_item):
            if isinstance(suite_item, unittest.TestCase):
                module_name = suite_item.__class__.__module__
                if "integration" not in module_name:
                    filtered_suite.addTest(suite_item)
            else:
                for item in suite_item:
                    filter_tests(item)
        filter_tests(suite)
        suite = filtered_suite



    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n====================================================")
    print("                  Test Summary                      ")
    print("====================================================")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("====================================================")

    # Exit with code 1 if any failure or error occurred
    if not result.wasSuccessful():
        print("[FAIL] One or more tests failed.")
        sys.exit(1)
    else:
        print("[SUCCESS] All tests passed successfully!")
        sys.exit(0)

if __name__ == '__main__':
    main()
