from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from database import db, Pedido, ItemPedido, Preco
from datetime import datetime
from fpdf import FPDF
import os
import json
import traceback

app = Flask(__name__)
app.config['SECRET_KEY'] = 'madeireira2026'

# ========== BANCO DE DADOS ==========
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///madeireira.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ========== CONFIGURAÇÕES ==========
CONFIG = {
    'nome': 'MADEIREIRA VIEIRA SOUZA',
    'endereco': 'BR 412',
    'telefone': '(11) 99999-9999',
    'email': 'contato@madeireira.com',
    'cnpj': '00.000.000/0001-00'
}

# ========== PREÇOS PADRÃO ==========
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

# ========== CRIAR BANCO ==========
with app.app_context():
    db.create_all()
    if Preco.query.count() == 0:
        for nome, preco in PRECOS_PADRAO.items():
            tipo = 'personalizado' if nome == 'Tábua 20+' else 'fixo'
            db.session.add(Preco(nome=nome, preco=preco, tipo=tipo))
        db.session.commit()
        print("✅ Banco de dados criado e preços carregados!")

# ==================== ROTAS ====================

@app.route('/')
def index():
    total_pedidos = Pedido.query.count()
    total_faturamento = db.session.query(db.func.sum(Pedido.total_liquido)).scalar() or 0
    pedidos_hoje = Pedido.query.filter_by(data=datetime.now().strftime('%d/%m/%Y')).count()
    ultimos_pedidos = Pedido.query.order_by(Pedido.id.desc()).limit(10).all()
    
    return render_template('index.html', 
                         config=CONFIG,
                         total_pedidos=total_pedidos,
                         total_faturamento=total_faturamento,
                         pedidos_hoje=pedidos_hoje,
                         ultimos_pedidos=ultimos_pedidos)

@app.route('/novo_pedido', methods=['GET', 'POST'])
def novo_pedido():
    if request.method == 'POST':
        try:
            print("=" * 50)
            print("📝 RECEBENDO PEDIDO")
            print("=" * 50)
            
            # Coletar dados do cliente
            cliente_nome = request.form.get('cliente_nome')
            cliente_cpf = request.form.get('cliente_cpf')
            forma_pagamento = request.form.get('forma_pagamento')
            desconto = float(request.form.get('desconto') or 0)
            
            print(f"👤 Cliente: {cliente_nome}")
            print(f"💳 Pagamento: {forma_pagamento}")
            print(f"📊 Desconto: {desconto}%")
            
            # Coletar itens
            itens_json = request.form.get('itens_json')
            print(f"📦 JSON recebido: {itens_json[:200] if itens_json else 'NENHUM JSON!'}")
            
            if not itens_json:
                flash('❌ Erro: Nenhum item foi enviado!', 'danger')
                return redirect(url_for('novo_pedido'))
            
            itens = json.loads(itens_json)
            print(f"📦 Itens parseados: {len(itens)}")
            
            if not itens:
                flash('❌ Adicione pelo menos um produto!', 'danger')
                return redirect(url_for('novo_pedido'))
            
            # Calcular totais
            total_bruto = sum(item['subtotal'] for item in itens)
            total_liquido = total_bruto * (1 - desconto/100)
            
            print(f"💰 Total Bruto: R$ {total_bruto:.2f}")
            print(f"💰 Total Líquido: R$ {total_liquido:.2f}")
            
            # Criar pedido
            pedido = Pedido(
                cliente_nome=cliente_nome,
                cliente_cpf=cliente_cpf,
                forma_pagamento=forma_pagamento,
                desconto=desconto,
                total_bruto=total_bruto,
                total_liquido=total_liquido
            )
            db.session.add(pedido)
            db.session.flush()
            
            # Adicionar itens
            for item in itens:
                item_pedido = ItemPedido(
                    pedido_id=pedido.id,
                    tipo_produto=item['tipo_produto'],
                    nome_madeira=item['nome_madeira'],
                    comprimento=item['comprimento'],
                    quantidade=item['quantidade'],
                    preco_metro=item['preco_metro'],
                    subtotal=item['subtotal']
                )
                db.session.add(item_pedido)
                print(f"   ✅ Item: {item['tipo_produto']} - {item['nome_madeira']} - R$ {item['subtotal']:.2f}")
            
            db.session.commit()
            print(f"✅ Pedido #{pedido.id} salvo!")
            
            # Gerar PDF
            pdf_path = gerar_pdf(pedido.id)
            
            if pdf_path:
                flash(f'✅ Pedido #{pedido.id} criado com sucesso! PDF gerado.', 'success')
            else:
                flash(f'⚠️ Pedido #{pedido.id} criado, mas houve erro ao gerar PDF.', 'warning')
            
            # REDIRECIONAR PARA O HISTÓRICO
            return redirect(url_for('historico'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao criar pedido: {str(e)}', 'danger')
            print(f"❌ ERRO: {str(e)}")
            traceback.print_exc()
            return redirect(url_for('novo_pedido'))
    
    # GET - mostrar formulário
    precos = Preco.query.order_by(Preco.nome).all()
    return render_template('novo_pedido.html', 
                         config=CONFIG,
                         precos=precos,
                         pedido_criado=False)

@app.route('/get_preco/<nome_produto>')
def get_preco(nome_produto):
    produto = Preco.query.filter_by(nome=nome_produto).first()
    if produto:
        return jsonify({'preco': produto.preco, 'tipo': produto.tipo})
    return jsonify({'error': 'Produto não encontrado'}), 404

@app.route('/precos')
def ver_precos():
    precos = Preco.query.order_by(Preco.nome).all()
    return render_template('precos.html', config=CONFIG, precos=precos)

@app.route('/gerenciar_precos', methods=['GET', 'POST'])
def gerenciar_precos():
    if request.method == 'POST':
        try:
            produto_id = request.form.get('produto_id')
            novo_preco = float(request.form.get('novo_preco'))
            
            produto = Preco.query.get(produto_id)
            if produto:
                produto.preco = novo_preco
                db.session.commit()
                flash(f'✅ Preço de {produto.nome} atualizado para R$ {novo_preco:.2f}!', 'success')
            else:
                flash('❌ Produto não encontrado!', 'danger')
        except Exception as e:
            flash(f'❌ Erro: {str(e)}', 'danger')
        
        return redirect(url_for('gerenciar_precos'))
    
    precos = Preco.query.order_by(Preco.nome).all()
    return render_template('gerenciar_precos.html', config=CONFIG, precos=precos)

@app.route('/historico')
def historico():
    pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    total_pedidos = len(pedidos)
    total_faturamento = sum(p.total_liquido for p in pedidos)
    
    return render_template('historico.html', 
                         config=CONFIG,
                         pedidos=pedidos,
                         total_pedidos=total_pedidos,
                         total_faturamento=total_faturamento)

@app.route('/baixar_pdf/<int:pedido_id>')
def baixar_pdf(pedido_id):
    pdf_path = f'pdfs/pedido_{pedido_id}.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        pdf_path = gerar_pdf(pedido_id)
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        else:
            flash('❌ PDF não encontrado!', 'danger')
            return redirect(url_for('historico'))

@app.route('/visualizar_pdf/<int:pedido_id>')
def visualizar_pdf(pedido_id):
    pdf_path = f'pdfs/pedido_{pedido_id}.pdf'
    if os.path.exists(pdf_path):
        return send_file(pdf_path)
    else:
        pdf_path = gerar_pdf(pedido_id)
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path)
        else:
            flash('❌ PDF não encontrado!', 'danger')
            return redirect(url_for('historico'))

# ==================== FUNÇÃO GERAR PDF ====================

def gerar_pdf(pedido_id):
    """Gera um PDF profissional e detalhado para o pedido"""
    try:
        print("=" * 50)
        print(f"📝 GERANDO PDF - Pedido #{pedido_id}")
        print("=" * 50)
        
        pedido = Pedido.query.get(pedido_id)
        if not pedido:
            print(f"❌ Pedido {pedido_id} não encontrado!")
            return None
        
        itens = ItemPedido.query.filter_by(pedido_id=pedido_id).all()
        if not itens:
            print(f"❌ Pedido {pedido_id} não tem itens!")
            return None
        
        print(f"✅ Pedido: {pedido.cliente_nome}")
        print(f"✅ Itens: {len(itens)}")
        print(f"✅ Total: R$ {pedido.total_liquido:.2f}")
        
        # Criar PDF
        pdf = FPDF()
        pdf.add_page()
        
        # 1. CABEÇALHO
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(190, 10, CONFIG['nome'], 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(190, 5, CONFIG['endereco'], 0, 1, 'C')
        pdf.cell(190, 5, f'Telefone: {CONFIG["telefone"]}  |  Email: {CONFIG["email"]}', 0, 1, 'C')
        pdf.cell(190, 5, f'CNPJ: {CONFIG["cnpj"]}', 0, 1, 'C')
        pdf.line(10, 50, 200, 50)
        pdf.ln(5)
        
        # 2. TÍTULO
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(190, 10, f'PEDIDO Nº {pedido.id}', 0, 1, 'L')
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        pdf.cell(95, 6, f'Data: {pedido.data}', 0, 0, 'L')
        pdf.cell(95, 6, f'Pagamento: {pedido.forma_pagamento}', 0, 1, 'L')
        pdf.ln(3)
        
        # 3. DADOS DO CLIENTE
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(190, 8, 'DADOS DO CLIENTE', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(190, 6, f'Nome: {pedido.cliente_nome}', 0, 1, 'L')
        pdf.cell(190, 6, f'CPF/CNPJ: {pedido.cliente_cpf or "NÃO INFORMADO"}', 0, 1, 'L')
        pdf.ln(5)
        
        # 4. TABELA DE PRODUTOS
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(190, 8, 'DETALHAMENTO DOS PRODUTOS', 0, 1, 'L', True)
        pdf.ln(2)
        
        # Cabeçalho da tabela
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(180, 180, 180)
        pdf.cell(35, 8, 'TIPO', 1, 0, 'C', True)
        pdf.cell(30, 8, 'MADEIRA', 1, 0, 'C', True)
        pdf.cell(20, 8, 'COMPR. (m)', 1, 0, 'C', True)
        pdf.cell(15, 8, 'QTD', 1, 0, 'C', True)
        pdf.cell(25, 8, 'PREÇO/m', 1, 0, 'C', True)
        pdf.cell(25, 8, 'TOTAL', 1, 0, 'C', True)
        pdf.cell(20, 8, 'METROS', 1, 0, 'C', True)
        pdf.cell(20, 8, 'M³', 1, 1, 'C', True)
        
        # Linhas da tabela
        pdf.set_font('Arial', '', 8)
        linha = 0
        for item in itens:
            if pdf.get_y() > 250:
                pdf.add_page()
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(180, 180, 180)
                pdf.cell(35, 8, 'TIPO', 1, 0, 'C', True)
                pdf.cell(30, 8, 'MADEIRA', 1, 0, 'C', True)
                pdf.cell(20, 8, 'COMPR. (m)', 1, 0, 'C', True)
                pdf.cell(15, 8, 'QTD', 1, 0, 'C', True)
                pdf.cell(25, 8, 'PREÇO/m', 1, 0, 'C', True)
                pdf.cell(25, 8, 'TOTAL', 1, 0, 'C', True)
                pdf.cell(20, 8, 'METROS', 1, 0, 'C', True)
                pdf.cell(20, 8, 'M³', 1, 1, 'C', True)
                pdf.set_font('Arial', '', 8)
            
            metros_lineares = item.comprimento * item.quantidade
            largura_padrao = 0.30
            espessura_padrao = 0.05
            volume_m3 = metros_lineares * largura_padrao * espessura_padrao
            
            cor = (245, 245, 245) if linha % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(cor[0], cor[1], cor[2])
            
            pdf.cell(35, 7, item.tipo_produto, 1, 0, 'L', True)
            pdf.cell(30, 7, item.nome_madeira, 1, 0, 'L', True)
            pdf.cell(20, 7, f'{item.comprimento:.2f}', 1, 0, 'R', True)
            pdf.cell(15, 7, str(item.quantidade), 1, 0, 'C', True)
            pdf.cell(25, 7, f'R$ {item.preco_metro:.2f}', 1, 0, 'R', True)
            pdf.cell(25, 7, f'R$ {item.subtotal:.2f}', 1, 0, 'R', True)
            pdf.cell(20, 7, f'{metros_lineares:.2f}', 1, 0, 'R', True)
            pdf.cell(20, 7, f'{volume_m3:.3f}', 1, 1, 'R', True)
            linha += 1
        
        # 5. TOTAIS
        pdf.ln(3)
        total_metros = sum(item.comprimento * item.quantidade for item in itens)
        total_volume = total_metros * 0.30 * 0.05
        
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(150, 8, 'RESUMO DO PEDIDO', 0, 1, 'L', True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(150, 6, f'Total de Itens: {len(itens)}', 0, 1, 'L')
        pdf.cell(150, 6, f'Total de Metros Lineares: {total_metros:.2f} m', 0, 1, 'L')
        pdf.cell(150, 6, f'Total em m³ (aprox.): {total_volume:.3f} m³', 0, 1, 'L')
        pdf.ln(3)
        
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(180, 180, 180)
        pdf.cell(130, 9, ' ', 0, 0, 'R')
        pdf.cell(60, 9, 'VALORES', 0, 1, 'L', True)
        
        pdf.set_font('Arial', '', 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(130, 8, 'Total Bruto:', 0, 0, 'R')
        pdf.cell(60, 8, f'R$ {pedido.total_bruto:.2f}', 0, 1, 'L', True)
        
        if pedido.desconto > 0:
            pdf.cell(130, 8, f'Desconto ({pedido.desconto:.0f}%):', 0, 0, 'R')
            pdf.cell(60, 8, f'- R$ {pedido.total_bruto * (pedido.desconto/100):.2f}', 0, 1, 'L', True)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.set_fill_color(200, 230, 200)
        pdf.cell(130, 10, 'TOTAL LÍQUIDO:', 0, 0, 'R')
        pdf.cell(60, 10, f'R$ {pedido.total_liquido:.2f}', 0, 1, 'L', True)
        
        # 6. RODAPÉ
        pdf.ln(5)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(190, 5, f'Pedido gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        pdf.cell(190, 5, 'Este documento é uma nota fiscal simplificada.', 0, 1, 'C')
        
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(190, 8, '_____________________________________________', 0, 1, 'C')
        pdf.cell(190, 6, f'{CONFIG["nome"]} - Qualidade e Confiança', 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        
        # Salvar PDF
        os.makedirs('pdfs', exist_ok=True)
        pdf_path = os.path.join('pdfs', f'pedido_{pedido_id}.pdf')
        pdf.output(pdf_path)
        
        print(f"✅ PDF gerado: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {str(e)}")
        traceback.print_exc()
        return None

# ==================== INICIAR SERVIDOR ====================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SERVIDOR MADEIREIRA INICIADO!")
    print("=" * 50)
    print("📱 Acesse no PC: http://localhost:5000")
    print("📱 Acesse no celular: http://192.168.18.110:5000")
    print("=" * 50)
    print("📋 ROTAS DISPONÍVEIS:")
    print("   / - Dashboard")
    print("   /novo_pedido - Novo Pedido")
    print("   /historico - Histórico de Pedidos")
    print("   /precos - Tabela de Preços")
    print("   /gerenciar_precos - Gerenciar Preços")
    print("=" * 50)
    print("🛑 Para parar: CTRL+C")
    print("=" * 50)
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)