"""
Script temporário para corrigir coordenadas do endereço central
Converte Granada, Espanha → Granada, Uberlândia, MG
"""
import os
import googlemaps
from sqlalchemy import create_engine, text

# Configuração
GOOGLE_MAPS_API_KEY = "AIzaSyDO7fMZQKzwy1JoXje-8njAL3LpI7mnzFs"
DATABASE_URL = "postgresql://gasbot:password@postgres:5432/gasbot"
TENANT_ID = "6bf18c92-943e-43e9-a407-39a98e026165"

# Endereço completo com cidade e estado
ADDRESS = "Av Angelino Favato, 260, Granada, Uberlândia, MG, Brasil"

print("=" * 80)
print("🔧 CORREÇÃO DE COORDENADAS - Granada, Uberlândia")
print("=" * 80)

# Inicializar cliente Google Maps
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

print(f"\n🌎 Fazendo geocoding: {ADDRESS}")
print(f"   Filtros: cidade=Uberlândia, estado=MG, país=BR")

# Fazer geocoding COM filtros geográficos
try:
    result = gmaps.geocode(
        ADDRESS,
        language="pt-BR",
        components={
            'locality': 'Uberlândia',
            'administrative_area': 'MG',
            'country': 'BR'
        }
    )
except Exception as e:
    print(f"\n❌ Erro na API do Google Maps: {e}")
    exit(1)

if not result:
    print("\n❌ Endereço não encontrado! Tentando sem filtros...")
    result = gmaps.geocode(ADDRESS, language="pt-BR")

    if not result:
        print("❌ Endereço não encontrado nem sem filtros!")
        exit(1)

# Extrair coordenadas
location = result[0]['geometry']['location']
lat = location['lat']
lng = location['lng']
formatted_address = result[0]['formatted_address']

print(f"\n✅ Endereço encontrado:")
print(f"   📍 Formatado: {formatted_address}")
print(f"   📐 Latitude: {lat}")
print(f"   📐 Longitude: {lng}")

# Verificar se coordenadas estão em Uberlândia (MG)
if not (-19.5 < lat < -18.5 and -48.5 < lng < -47.5):
    print(f"\n⚠️  AVISO: Coordenadas fora da região esperada de Uberlândia!")
    print(f"   Latitude esperada: entre -19.5 e -18.5")
    print(f"   Longitude esperada: entre -48.5 e -47.5")
    print(f"   Coordenadas obtidas: {lat}, {lng}")
    print(f"\n   Pode ser que o Google Maps tenha retornado o endereço errado.")
    response = input("\n   Deseja continuar mesmo assim? (s/n): ")
    if response.lower() != 's':
        print("❌ Operação cancelada pelo usuário")
        exit(1)

# Atualizar banco de dados
print(f"\n📦 Conectando ao banco de dados...")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Buscar configs atuais
    result_db = conn.execute(text(f"""
        SELECT
            id,
            center_address,
            center_lat,
            center_lng,
            radius_km_start,
            radius_km_end
        FROM radius_configs
        WHERE tenant_id = '{TENANT_ID}'
    """))

    rows = result_db.fetchall()

    print(f"\n📊 Configurações atuais ({len(rows)} registros):")
    print(f"{'ID':<38} | {'Endereço':<35} | {'Lat':<12} | {'Lng':<12} | {'KM':<10}")
    print("-" * 120)

    for row in rows:
        print(f"{str(row[0]):<38} | {row[1][:35]:<35} | {row[2]:<12.8f} | {row[3]:<12.8f} | {row[4]}-{row[5]}km")

    # Atualizar
    print(f"\n🔄 Atualizando coordenadas...")
    conn.execute(text(f"""
        UPDATE radius_configs
        SET
            center_lat = {lat},
            center_lng = {lng},
            center_address = '{formatted_address}'
        WHERE tenant_id = '{TENANT_ID}'
    """))
    conn.commit()

    # Verificar atualização
    result_db_after = conn.execute(text(f"""
        SELECT
            id,
            center_address,
            center_lat,
            center_lng,
            radius_km_start,
            radius_km_end
        FROM radius_configs
        WHERE tenant_id = '{TENANT_ID}'
    """))

    rows_after = result_db_after.fetchall()

    print(f"\n✅ Configurações atualizadas ({len(rows_after)} registros):")
    print(f"{'ID':<38} | {'Endereço':<35} | {'Lat':<12} | {'Lng':<12} | {'KM':<10}")
    print("-" * 120)

    for row in rows_after:
        print(f"{str(row[0]):<38} | {row[1][:35]:<35} | {row[2]:<12.8f} | {row[3]:<12.8f} | {row[4]}-{row[5]}km")

print("\n" + "=" * 80)
print("🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 80)
print("\n📋 Próximos passos:")
print("   1. Restart do backend: docker-compose restart backend")
print("   2. Teste via WhatsApp: 'Av Angelino Favato 150, Granada'")
print("   3. Verificar distância calculada (deve ser < 1km)")
print("\n✅ Script pode ser deletado após confirmação do funcionamento\n")
