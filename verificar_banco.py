from app import app
from database import db, Preco

with app.app_context():
    total = Preco.query.count()
    print(f"Total de preços no banco: {total}")
    
    if total > 0:
        print("\nPreços cadastrados:")
        for p in Preco.query.all():
            print(f"  {p.nome}: R$ {p.preco:.2f} ({p.tipo})")
    else:
        print("❌ Nenhum preço cadastrado!")