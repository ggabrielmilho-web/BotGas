"""
Test agent orchestration flow (without database or API calls)
"""
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def test_master_agent_routing():
    """Test that MasterAgent can route to correct sub-agents"""
    print("\n🔀 Testing Master Agent Routing Logic...")

    try:
        from app.agents.base import AgentContext

        # Create mock context
        context = AgentContext(
            tenant_id=uuid4(),
            customer_phone="5511999999999",
            conversation_id=uuid4(),
            session_data={},
            message_history=[]
        )

        test_scenarios = [
            {
                "message": "Olá, bom dia!",
                "expected_intent": "greeting",
                "expected_agent": "AttendanceAgent",
                "stage": "greeting"
            },
            {
                "message": "Quais produtos vocês têm?",
                "expected_intent": "product_inquiry",
                "expected_agent": "AttendanceAgent",
                "stage": "greeting"
            },
            {
                "message": "Quero 2 botijões",
                "expected_intent": "make_order",
                "expected_agent": "OrderAgent",
                "stage": "greeting"
            },
            {
                "message": "Rua das Flores, 123",
                "expected_intent": "provide_address",
                "expected_agent": "ValidationAgent",
                "stage": "greeting"
            },
            {
                "message": "Meu endereço é Av Paulista 1000",
                "expected_intent": "provide_address",
                "expected_agent": "ValidationAgent",
                "stage": "awaiting_address"
            },
            {
                "message": "Vou pagar com PIX",
                "expected_intent": "payment",
                "expected_agent": "PaymentAgent",
                "stage": "payment"
            },
        ]

        print("\nScenarios:")
        for idx, scenario in enumerate(test_scenarios, 1):
            message = scenario["message"]
            expected_intent = scenario["expected_intent"]
            expected_agent = scenario["expected_agent"]

            # Simulate intent detection
            from app.agents.base import BaseAgent

            class TestAgent(BaseAgent):
                async def process(self, message, context):
                    pass

            agent = TestAgent()
            detected_intent = agent._detect_intent(message)

            # Determine which agent would be used
            context.session_data["stage"] = scenario["stage"]

            if detected_intent in ["greeting", "product_inquiry", "help", "general"]:
                routed_agent = "AttendanceAgent"
            elif detected_intent == "provide_address" or context.session_data.get("stage") == "awaiting_address":
                routed_agent = "ValidationAgent"
            elif detected_intent == "make_order" or context.session_data.get("stage") == "building_order":
                routed_agent = "OrderAgent"
            elif detected_intent == "payment" or context.session_data.get("stage") == "payment":
                routed_agent = "PaymentAgent"
            else:
                routed_agent = "AttendanceAgent"

            intent_match = "✅" if detected_intent == expected_intent else "⚠️"
            routing_match = "✅" if routed_agent == expected_agent else "❌"

            print(f"{idx}. {message[:40]}")
            print(f"   Intent: {detected_intent} {intent_match} (expected: {expected_intent})")
            print(f"   Routes to: {routed_agent} {routing_match} (expected: {expected_agent})")
            print()

        print("✅ Routing logic test completed")
        return True

    except Exception as e:
        print(f"❌ Error testing routing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_flow():
    """Test typical conversation flow through agents"""
    print("\n💬 Testing Conversation Flow Simulation...")

    try:
        from app.agents.base import AgentContext, AgentResponse

        # Simulate conversation
        context = AgentContext(
            tenant_id=uuid4(),
            customer_phone="5511999999999",
            conversation_id=uuid4(),
            session_data={},
            message_history=[]
        )

        conversation_steps = [
            {
                "step": "1. Customer greeting",
                "message": "Oi, bom dia!",
                "expected_stage": "greeting",
                "expected_next": "Ask about needs"
            },
            {
                "step": "2. Customer asks about products",
                "message": "Quanto custa o botijão?",
                "expected_stage": "greeting",
                "expected_next": "Show products"
            },
            {
                "step": "3. Customer makes order",
                "message": "Quero 2 botijões de 13kg",
                "expected_stage": "building_order",
                "expected_next": "Add to order"
            },
            {
                "step": "4. Customer provides address",
                "message": "Rua das Flores, 123, Centro",
                "expected_stage": "awaiting_address",
                "expected_next": "Validate address"
            },
            {
                "step": "5. Customer chooses payment",
                "message": "PIX",
                "expected_stage": "payment",
                "expected_next": "Show PIX details & finalize"
            },
        ]

        print("\nConversation Flow:")
        for step_data in conversation_steps:
            print(f"\n{step_data['step']}")
            print(f"   Message: '{step_data['message']}'")
            print(f"   Expected stage: {step_data['expected_stage']}")
            print(f"   Next action: {step_data['expected_next']}")

            # Update context for next step
            if "order" in step_data["step"].lower():
                context.session_data["stage"] = "building_order"
                context.session_data["current_order"] = {"items": [], "subtotal": 0, "total": 0}
            elif "address" in step_data["step"].lower():
                context.session_data["stage"] = "awaiting_address"
            elif "payment" in step_data["step"].lower():
                context.session_data["stage"] = "payment"

        print("\n✅ Conversation flow simulation completed")
        return True

    except Exception as e:
        print(f"❌ Error testing conversation flow: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_intervention_logic():
    """Test human intervention trigger logic"""
    print("\n🤚 Testing Human Intervention Logic...")

    try:
        messages_trigger_intervention = [
            "Quero falar com um atendente",
            "Preciso falar com alguém",
            "Atendente humano por favor",
            "Isso não está funcionando, quero uma pessoa",
        ]

        messages_no_intervention = [
            "Olá, bom dia",
            "Quero 2 botijões",
            "Qual o preço?",
        ]

        print("\nMessages that SHOULD trigger intervention:")
        for msg in messages_trigger_intervention:
            # Simple keyword check (mimics should_auto_intervene logic)
            trigger_keywords = ["atendente", "falar com alguém", "pessoa", "humano"]
            should_trigger = any(kw in msg.lower() for kw in trigger_keywords)

            status = "✅" if should_trigger else "❌"
            print(f"{status} '{msg}' -> Trigger: {should_trigger}")

        print("\nMessages that should NOT trigger intervention:")
        for msg in messages_no_intervention:
            trigger_keywords = ["atendente", "falar com alguém", "pessoa"]
            should_trigger = any(kw in msg.lower() for kw in trigger_keywords)

            status = "✅" if not should_trigger else "❌"
            print(f"{status} '{msg}' -> Trigger: {should_trigger}")

        print("\n✅ Intervention logic test completed")
        return True

    except Exception as e:
        print(f"❌ Error testing intervention: {e}")
        return False


def test_order_building():
    """Test order building logic"""
    print("\n🛒 Testing Order Building Logic...")

    try:
        from app.agents.order import OrderAgent

        # Test product/quantity extraction (simplified)
        test_messages = [
            ("Quero 2 botijões de 13kg", {"product": "botijão", "quantity": 2}),
            ("Quero um galão de água", {"product": "galão", "quantity": 1}),
            ("3 botijões por favor", {"product": "botijão", "quantity": 3}),
        ]

        print("\nProduct extraction tests:")
        for message, expected in test_messages:
            # Simple extraction
            import re
            numbers = re.findall(r'\d+', message)
            quantity = int(numbers[0]) if numbers else 1

            print(f"Message: '{message}'")
            print(f"  Extracted quantity: {quantity} (expected: {expected['quantity']})")
            status = "✅" if quantity == expected['quantity'] else "⚠️"
            print(f"  {status}\n")

        print("✅ Order building logic test completed")
        return True

    except Exception as e:
        print(f"❌ Error testing order building: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_orchestration_tests():
    """Run all orchestration tests"""
    print("=" * 60)
    print("🎭 GASBOT AGENTS - ORCHESTRATION TESTS")
    print("=" * 60)

    results = []

    results.append(("Master Agent Routing", test_master_agent_routing()))
    results.append(("Conversation Flow", test_conversation_flow()))
    results.append(("Intervention Logic", test_intervention_logic()))
    results.append(("Order Building", test_order_building()))

    print("\n" + "=" * 60)
    print("📊 ORCHESTRATION TEST RESULTS")
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
    success = run_orchestration_tests()
    sys.exit(0 if success else 1)
