from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(20), default=datetime.now().strftime('%d/%m/%Y'))
    cliente_nome = db.Column(db.String(100), nullable=False)
    cliente_cpf = db.Column(db.String(20))
    forma_pagamento = db.Column(db.String(50))
    desconto = db.Column(db.Float, default=0.0)
    total_bruto = db.Column(db.Float, default=0.0)
    total_liquido = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.String(30), default=datetime.now().strftime('%d/%m/%Y %H:%M'))
    
    # Relacionamento com os itens
    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade='all, delete-orphan')


class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    tipo_produto = db.Column(db.String(50), nullable=False)
    nome_madeira = db.Column(db.String(50), nullable=False)
    comprimento = db.Column(db.Float, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_metro = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)


class Preco(db.Model):
    __tablename__ = 'precos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20), default='fixo')