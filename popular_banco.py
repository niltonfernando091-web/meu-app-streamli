from app import app
from database import db, Preco

PRECOS_PADRAO = {
    'Linha 14': 31.00,
    'Linha 10': 25.00,
    'Linha 12': 28.00,
    'Linha 20': 51.00,
    'Linha 30': 79.00,
    'Caibo 6,5': 6.50,
    'Ripa 3,25': 3.25,
    'Tábua 14': 18.00,
    'Tábua 12': 15.50,
    'Tábua 10': 13.00,
    'Tábua 20+': 0.0,
    'Estaca 10x10': 58.00
}

with app.app_context():
    # Verificar quantos preços existem
    total = Preco.query.count()
    print(f"Preços existentes: {total}")
    
    if total == 0:
        print("📝 Cadastrando preços padrão...")
        for nome, preco in PRECOS_PADRAO.items():
            tipo = 'personalizado' if nome == 'Tábua 20+' else 'fixo'
            novo_preco = Preco(nome=nome, preco=preco, tipo=tipo)
            db.session.add(novo_preco)
        db.session.commit()
        print(f"✅ {Preco.query.count()} preços cadastrados com sucesso!")
    else:
        print("ℹ️  Os preços já estão cadastrados.")
    
    # Mostrar os preços
    print("\n📋 Preços atuais:")
    for p in Preco.query.order_by(Preco.nome).all():
        print(f"  {p.nome}: R$ {p.preco:.2f} ({p.tipo})")