"""
Run all agent tests - combines basic and orchestration tests
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def main():
    print("\n")
    print("=" * 60)
    print(" " * 15 + "GASBOT AGENT TEST SUITE")
    print("=" * 60)
    print()

    all_passed = True

    # Test 1: Basic Structure
    print("\n" + ">" * 60)
    print("Part 1: Basic Structure Tests")
    print(">" * 60)

    try:
        from test_agents_basic import run_all_tests as run_basic_tests
        basic_passed = run_basic_tests()
        all_passed = all_passed and basic_passed
    except Exception as e:
        print(f"❌ Error running basic tests: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Test 2: Orchestration
    print("\n" + ">" * 60)
    print("Part 2: Orchestration Tests")
    print(">" * 60)

    try:
        from test_agent_orchestration import run_orchestration_tests
        orchestration_passed = run_orchestration_tests()
        all_passed = all_passed and orchestration_passed
    except Exception as e:
        print(f"❌ Error running orchestration tests: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Final Summary
    print("\n")
    print("=" * 60)
    print(" " * 18 + "FINAL SUMMARY")
    print("=" * 60)

    if all_passed:
        print("  ALL TESTS PASSED!")
        print("  The agent system structure is working correctly.")
    else:
        print("  SOME TESTS FAILED")
        print("  Review the errors above for details.")

    print("=" * 60)
    print()

    print("Next Steps:")
    print("   1. Fix any import errors")
    print("   2. Add database models (Session 2)")
    print("   3. Configure environment variables (.env)")
    print("   4. Test with actual OpenAI API key")
    print("   5. Test with mock database")
    print()

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
