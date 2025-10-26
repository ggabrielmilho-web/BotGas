"""
Script para encerrar conversas ativas
"""
import sys
sys.path.insert(0, 'c:/Phyton-Projetos/BotGas/backend')

from app.database.base import SessionLocal
from app.database.models import Conversation
from datetime import datetime

def close_active_conversations():
    db = SessionLocal()
    try:
        # Buscar conversas ativas
        conversations = db.query(Conversation).filter(
            Conversation.status == 'active'
        ).all()

        if not conversations:
            print("❌ Nenhuma conversa ativa encontrada")
            return

        print(f"📋 Encontradas {len(conversations)} conversa(s) ativa(s):\n")

        for conv in conversations:
            print(f"  ID: {conv.id}")
            print(f"  Session ID: {conv.session_id}")
            print(f"  Started: {conv.started_at}")
            print(f"  Messages: {conv.total_messages}")
            print()

        # Encerrar todas
        for conv in conversations:
            conv.status = 'completed'
            conv.ended_at = datetime.utcnow()

        db.commit()
        print(f"✅ {len(conversations)} conversa(s) encerrada(s) com sucesso!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    close_active_conversations()
