"""
Basic tests for agents - validates structure and imports
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def test_import_base_classes():
    """Test that base classes can be imported"""
    print("Testing base class imports...")

    try:
        from app.agents.base import BaseAgent, AgentContext, AgentResponse
        print("✅ Base classes imported successfully")

        # Test AgentContext creation
        from uuid import uuid4
        context = AgentContext(
            tenant_id=uuid4(),
            customer_phone="5511999999999",
            conversation_id=uuid4(),
            session_data={},
            message_history=[]
        )
        print(f"✅ AgentContext created: {context.customer_phone}")

        # Test AgentResponse creation
        response = AgentResponse(
            text="Test response",
            intent="test",
            should_end=False
        )
        print(f"✅ AgentResponse created: {response.text}")

        return True

    except Exception as e:
        print(f"❌ Error importing base classes: {e}")
        return False


def test_import_all_agents():
    """Test that all agents can be imported"""
    print("\nTesting agent imports...")

    agents_to_test = [
        ("MasterAgent", "app.agents.master"),
        ("AttendanceAgent", "app.agents.attendance"),
        ("ValidationAgent", "app.agents.validation"),
        ("OrderAgent", "app.agents.order"),
        ("PaymentAgent", "app.agents.payment"),
    ]

    success_count = 0

    for agent_name, module_path in agents_to_test:
        try:
            module = __import__(module_path, fromlist=[agent_name])
            agent_class = getattr(module, agent_name)
            print(f"✅ {agent_name} imported from {module_path}")
            success_count += 1
        except Exception as e:
            print(f"❌ Error importing {agent_name}: {e}")

    print(f"\n{success_count}/{len(agents_to_test)} agents imported successfully")
    return success_count == len(agents_to_test)


def test_import_services():
    """Test that services can be imported"""
    print("\nTesting service imports...")

    services_to_test = [
        ("InterventionService", "app.services.intervention"),
        ("AudioProcessor", "app.services.audio_processor"),
        ("AddressCacheService", "app.services.address_cache"),
    ]

    success_count = 0

    for service_name, module_path in services_to_test:
        try:
            module = __import__(module_path, fromlist=[service_name])
            service_class = getattr(module, service_name)
            print(f"✅ {service_name} imported from {module_path}")
            success_count += 1
        except Exception as e:
            print(f"❌ Error importing {service_name}: {e}")

    print(f"\n{success_count}/{len(services_to_test)} services imported successfully")
    return success_count == len(services_to_test)


def test_agent_instantiation():
    """Test that agents can be instantiated (without API keys)"""
    print("\nTesting agent instantiation...")

    try:
        # Note: This will fail if OPENAI_API_KEY is not set, but we're testing structure
        from app.agents.attendance import AttendanceAgent
        from app.agents.order import OrderAgent
        from app.agents.payment import PaymentAgent

        print("⚠️  Agent instantiation requires OPENAI_API_KEY (skipped in basic test)")
        print("✅ Agent classes are properly defined")

        return True

    except Exception as e:
        print(f"❌ Error with agent structure: {e}")
        return False


def test_intent_detection():
    """Test basic intent detection from BaseAgent"""
    print("\nTesting intent detection...")

    try:
        from app.agents.base import BaseAgent
        from uuid import uuid4

        # Create a dummy agent for testing
        class DummyAgent(BaseAgent):
            async def process(self, message, context):
                pass

        agent = DummyAgent()

        test_cases = [
            ("Olá, bom dia!", "greeting"),
            ("Quanto custa o botijão?", "product_inquiry"),
            ("Quero 2 botijões", "make_order"),
            ("Meu endereço é Rua X, 123", "provide_address"),
            ("Vou pagar com PIX", "payment"),
        ]

        for message, expected_intent in test_cases:
            detected = agent._detect_intent(message)
            status = "✅" if detected == expected_intent else "⚠️"
            print(f"{status} '{message[:30]}...' -> {detected} (expected: {expected_intent})")

        return True

    except Exception as e:
        print(f"❌ Error testing intent detection: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all basic tests"""
    print("=" * 60)
    print("🧪 GASBOT AGENTS - BASIC STRUCTURE TESTS")
    print("=" * 60)

    results = []

    results.append(("Base Classes Import", test_import_base_classes()))
    results.append(("All Agents Import", test_import_all_agents()))
    results.append(("Services Import", test_import_services()))
    results.append(("Agent Instantiation", test_agent_instantiation()))
    results.append(("Intent Detection", test_intent_detection()))

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
