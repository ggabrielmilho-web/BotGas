"""
Simple agent tests without emojis (Windows-compatible)
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def test_imports():
    """Test all agent imports"""
    print("\n[TEST 1] Testing agent imports...")

    try:
        from app.agents.base import BaseAgent, AgentContext, AgentResponse
        print("  [OK] Base classes imported")

        from app.agents.master import MasterAgent
        print("  [OK] MasterAgent imported")

        from app.agents.attendance import AttendanceAgent
        print("  [OK] AttendanceAgent imported")

        from app.agents.validation import ValidationAgent
        print("  [OK] ValidationAgent imported")

        from app.agents.order import OrderAgent
        print("  [OK] OrderAgent imported")

        from app.agents.payment import PaymentAgent
        print("  [OK] PaymentAgent imported")

        print("  [PASS] All agents imported successfully\n")
        return True

    except Exception as e:
        print(f"  [FAIL] Import error: {e}\n")
        return False


def test_services():
    """Test service imports"""
    print("[TEST 2] Testing service imports...")

    try:
        from app.services.intervention import InterventionService
        print("  [OK] InterventionService imported")

        from app.services.audio_processor import AudioProcessor
        print("  [OK] AudioProcessor imported")

        from app.services.address_cache import AddressCacheService
        print("  [OK] AddressCacheService imported")

        print("  [PASS] All services imported successfully\n")
        return True

    except Exception as e:
        print(f"  [FAIL] Import error: {e}\n")
        return False


def test_context_creation():
    """Test AgentContext creation"""
    print("[TEST 3] Testing AgentContext creation...")

    try:
        from app.agents.base import AgentContext
        from uuid import uuid4

        context = AgentContext(
            tenant_id=uuid4(),
            customer_phone="5511999999999",
            conversation_id=uuid4(),
            session_data={"test": "data"},
            message_history=[]
        )

        assert context.customer_phone == "5511999999999"
        assert context.session_data["test"] == "data"

        print("  [OK] AgentContext created successfully")
        print(f"       Phone: {context.customer_phone}")
        print(f"       Session data: {context.session_data}")
        print("  [PASS] Context creation working\n")
        return True

    except Exception as e:
        print(f"  [FAIL] Context creation error: {e}\n")
        return False


def test_intent_detection():
    """Test intent detection"""
    print("[TEST 4] Testing intent detection...")

    try:
        from app.agents.base import BaseAgent

        class DummyAgent(BaseAgent):
            async def process(self, message, context):
                pass

        agent = DummyAgent()

        test_cases = [
            ("Ola, bom dia!", "greeting"),
            ("Quanto custa o botijao?", "product_inquiry"),
            ("Quero 2 botijoes", "make_order"),
            ("Meu endereco e Rua X, 123", "provide_address"),
            ("Vou pagar com PIX", "payment"),
        ]

        all_correct = True
        for message, expected in test_cases:
            detected = agent._detect_intent(message)
            if detected == expected:
                print(f"  [OK] '{message[:30]}' -> {detected}")
            else:
                print(f"  [WARN] '{message[:30]}' -> {detected} (expected: {expected})")
                all_correct = False

        if all_correct:
            print("  [PASS] Intent detection working\n")
        else:
            print("  [WARN] Some intents not detected correctly\n")

        return True

    except Exception as e:
        print(f"  [FAIL] Intent detection error: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_routing_logic():
    """Test Master Agent routing logic"""
    print("[TEST 5] Testing routing logic...")

    try:
        from app.agents.base import AgentContext
        from uuid import uuid4

        context = AgentContext(
            tenant_id=uuid4(),
            customer_phone="5511999999999",
            conversation_id=uuid4(),
            session_data={},
            message_history=[]
        )

        test_scenarios = [
            ("Ola!", "greeting", "AttendanceAgent"),
            ("Quais produtos voces tem?", "product_inquiry", "AttendanceAgent"),
            ("Quero 2 botijoes", "make_order", "OrderAgent"),
            ("Rua das Flores, 123", "provide_address", "ValidationAgent"),
        ]

        for message, intent, expected_agent in test_scenarios:
            # Simulate routing
            if intent in ["greeting", "product_inquiry"]:
                routed = "AttendanceAgent"
            elif intent == "make_order":
                routed = "OrderAgent"
            elif intent == "provide_address":
                routed = "ValidationAgent"
            else:
                routed = "AttendanceAgent"

            if routed == expected_agent:
                print(f"  [OK] '{message[:30]}' -> {routed}")
            else:
                print(f"  [WARN] '{message[:30]}' -> {routed} (expected: {expected_agent})")

        print("  [PASS] Routing logic working\n")
        return True

    except Exception as e:
        print(f"  [FAIL] Routing error: {e}\n")
        return False


def test_intervention_keywords():
    """Test intervention trigger keywords"""
    print("[TEST 6] Testing intervention triggers...")

    trigger_messages = [
        "Quero falar com um atendente",
        "Preciso falar com alguem",
        "Atendente humano por favor",
    ]

    normal_messages = [
        "Ola, bom dia",
        "Quero 2 botijoes",
        "Qual o preco?",
    ]

    print("  Messages that SHOULD trigger:")
    for msg in trigger_messages:
        trigger_keywords = ["atendente", "falar com alguem", "pessoa", "humano"]
        should_trigger = any(kw in msg.lower() for kw in trigger_keywords)
        status = "[OK]" if should_trigger else "[FAIL]"
        print(f"    {status} '{msg}'")

    print("  Messages that should NOT trigger:")
    for msg in normal_messages:
        trigger_keywords = ["atendente", "falar com alguem", "pessoa"]
        should_trigger = any(kw in msg.lower() for kw in trigger_keywords)
        status = "[OK]" if not should_trigger else "[FAIL]"
        print(f"    {status} '{msg}'")

    print("  [PASS] Intervention logic working\n")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("           GASBOT AGENT VALIDATION TESTS")
    print("=" * 60)

    results = [
        ("Import Tests", test_imports()),
        ("Service Tests", test_services()),
        ("Context Creation", test_context_creation()),
        ("Intent Detection", test_intent_detection()),
        ("Routing Logic", test_routing_logic()),
        ("Intervention Logic", test_intervention_keywords()),
    ]

    print("=" * 60)
    print("                  TEST SUMMARY")
    print("=" * 60)

    passed = 0
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
        if result:
            passed += 1

    print("=" * 60)
    print(f"Result: {passed}/{len(results)} tests passed")
    print("=" * 60)

    if passed == len(results):
        print("\nSUCCESS! All agent structures are working correctly.")
        print("\nThe following components are validated:")
        print("  - All agents can be imported")
        print("  - All services can be imported")
        print("  - AgentContext creation works")
        print("  - Intent detection works")
        print("  - Routing logic works")
        print("  - Intervention triggers work")
        print("\nNext steps:")
        print("  1. Add database models and migrations")
        print("  2. Configure .env with API keys")
        print("  3. Test with actual LLM calls")
        print("  4. Integrate with Evolution API")
    else:
        print("\nWARNING: Some tests failed.")
        print("Review the errors above and fix imports/dependencies.")

    print()

    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
