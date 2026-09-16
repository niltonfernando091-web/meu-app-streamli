// ============================================
// SISTEMA DE VENDAS - MADEIREIRA
// ============================================

let itens = [];
let totalBruto = 0;

document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ JavaScript carregado!");
    
    // Máscara para CPF
    const cpfInput = document.getElementById('cliente_cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
                e.target.value = value;
            }
        });
    }

    // Carregar preço ao selecionar produto
    const tipoProduto = document.getElementById('tipo_produto');
    if (tipoProduto) {
        tipoProduto.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const preco = selectedOption.dataset.preco;
            const tipo = selectedOption.dataset.tipo;
            const precoInput = document.getElementById('preco_metro');
            const divPersonalizado = document.getElementById('preco_personalizado');
            
            if (tipo === 'personalizado') {
                divPersonalizado.style.display = 'block';
                precoInput.value = 0;
                document.getElementById('largura_cm').value = '';
            } else {
                divPersonalizado.style.display = 'none';
                precoInput.value = preco;
            }
        });
    }

    // Tábua 20+ - calcular preço pela largura
    const larguraCm = document.getElementById('largura_cm');
    if (larguraCm) {
        larguraCm.addEventListener('input', function() {
            const largura = parseFloat(this.value);
            if (largura >= 20) {
                document.getElementById('preco_metro').value = largura;
            }
        });
    }

    // Botão Adicionar Item
    const btnAdicionar = document.getElementById('btnAdicionarItem');
    if (btnAdicionar) {
        btnAdicionar.addEventListener('click', adicionarItem);
    }

    // Enter para adicionar
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.target.closest('#formPedido')) {
            e.preventDefault();
            adicionarItem();
        }
    });

    // Atualizar total quando desconto mudar
    const descontoInput = document.getElementById('desconto');
    if (descontoInput) {
        descontoInput.addEventListener('input', atualizarTotal);
    }

    // ============================================
    // ENVIO DO FORMULÁRIO
    // ============================================
    const form = document.getElementById('formPedido');
    if (form) {
        console.log("✅ Formulário encontrado!");
        
        form.addEventListener('submit', function(e) {
            console.log("📤 Enviando formulário...");
            console.log(`📦 Itens no pedido: ${itens.length}`);
            
            // VALIDAÇÕES
            if (itens.length === 0) {
                e.preventDefault();
                alert('⚠️ Adicione pelo menos um item ao pedido!');
                return false;
            }
            
            const clienteNome = document.getElementById('cliente_nome');
            if (!clienteNome.value.trim()) {
                e.preventDefault();
                alert('⚠️ Digite o nome do cliente!');
                clienteNome.focus();
                return false;
            }
            
            const formaPagamento = document.getElementById('forma_pagamento');
            if (!formaPagamento.value) {
                e.preventDefault();
                alert('⚠️ Selecione a forma de pagamento!');
                formaPagamento.focus();
                return false;
            }
            
            // REMOVER CAMPO ANTERIOR SE EXISTIR
            const campoExistente = document.querySelector('input[name="itens_json"]');
            if (campoExistente) {
                campoExistente.remove();
            }
            
            // CRIAR CAMPO COM OS ITENS EM JSON
            const inputItens = document.createElement('input');
            inputItens.type = 'hidden';
            inputItens.name = 'itens_json';
            inputItens.value = JSON.stringify(itens);
            this.appendChild(inputItens);
            
            console.log("✅ Dados preparados para envio:");
            console.log(`   Cliente: ${clienteNome.value}`);
            console.log(`   Itens: ${itens.length}`);
            console.log(`   Total: R$ ${totalBruto.toFixed(2)}`);
            
            return true;
        });
    } else {
        console.error("❌ Formulário não encontrado!");
    }
});

// ============================================
// FUNÇÃO: Adicionar Item
// ============================================
function adicionarItem() {
    console.log("➕ Adicionando item...");
    
    const tipoProduto = document.getElementById('tipo_produto');
    const nomeMadeira = document.getElementById('nome_madeira');
    const comprimento = document.getElementById('comprimento');
    const quantidade = document.getElementById('quantidade');
    const precoMetro = document.getElementById('preco_metro');
    const divPersonalizado = document.getElementById('preco_personalizado');
    const larguraCm = document.getElementById('largura_cm');

    // Validações
    if (!tipoProduto.value) {
        alert('⚠️ Selecione um tipo de produto!');
        tipoProduto.focus();
        return;
    }

    if (!nomeMadeira.value.trim()) {
        alert('⚠️ Digite o nome da madeira!');
        nomeMadeira.focus();
        return;
    }

    if (!comprimento.value || parseFloat(comprimento.value) <= 0) {
        alert('⚠️ Digite um comprimento válido!');
        comprimento.focus();
        return;
    }

    if (!quantidade.value || parseInt(quantidade.value) <= 0) {
        alert('⚠️ Digite uma quantidade válida!');
        quantidade.focus();
        return;
    }

    // Tábua 20+
    if (divPersonalizado.style.display === 'block') {
        if (!larguraCm.value || parseFloat(larguraCm.value) < 20) {
            alert('⚠️ Para Tábua 20+, digite a largura (mínimo 20cm)!');
            larguraCm.focus();
            return;
        }
        precoMetro.value = parseFloat(larguraCm.value);
    }

    const preco = parseFloat(precoMetro.value);
    if (!preco || preco <= 0) {
        alert('⚠️ Preço inválido!');
        return;
    }

    const comp = parseFloat(comprimento.value);
    const qtd = parseInt(quantidade.value);
    const subtotal = comp * qtd * preco;

    // Criar item
    const item = {
        tipo_produto: tipoProduto.value,
        nome_madeira: nomeMadeira.value.trim(),
        comprimento: comp,
        quantidade: qtd,
        preco_metro: preco,
        subtotal: subtotal
    };

    itens.push(item);
    totalBruto += subtotal;

    console.log(`✅ Item adicionado: ${item.tipo_produto} - ${item.nome_madeira}`);
    console.log(`   Subtotal: R$ ${item.subtotal.toFixed(2)}`);

    atualizarTabela();
    atualizarTotal();

    // Limpar campos
    nomeMadeira.value = '';
    comprimento.value = '';
    quantidade.value = 1;
    if (divPersonalizado.style.display === 'block') {
        larguraCm.value = '';
        precoMetro.value = 0;
    }
    tipoProduto.focus();
}

// ============================================
// FUNÇÃO: Atualizar Tabela
// ============================================
function atualizarTabela() {
    const tbody = document.querySelector('#tabelaItens tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (itens.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted py-3">
                    <i class="bi bi-inbox"></i> Nenhum item adicionado
                </td>
            </tr>
        `;
        document.getElementById('contadorItens').textContent = '0 itens';
        return;
    }

    itens.forEach((item, index) => {
        const row = document.createElement('tr');
        row.className = 'item-row';
        row.innerHTML = `
            <td><strong>${item.tipo_produto}</strong></td>
            <td>${item.nome_madeira}</td>
            <td class="text-end">${item.comprimento.toFixed(2)}</td>
            <td class="text-end">${item.quantidade}</td>
            <td class="text-end">R$ ${item.preco_metro.toFixed(2)}</td>
            <td class="text-end">
                <strong>R$ ${item.subtotal.toFixed(2)}</strong>
            </td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-danger" onclick="removerItem(${index})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById('contadorItens').textContent = `${itens.length} itens`;
}

// ============================================
// FUNÇÃO: Remover Item
// ============================================
function removerItem(index) {
    totalBruto -= itens[index].subtotal;
    itens.splice(index, 1);
    atualizarTabela();
    atualizarTotal();
    console.log(`🗑️ Item removido. Restam: ${itens.length}`);
}

// ============================================
// FUNÇÃO: Atualizar Total
// ============================================
function atualizarTotal() {
    const desconto = parseFloat(document.getElementById('desconto').value) || 0;
    const totalLiquido = totalBruto * (1 - desconto / 100);
    
    document.getElementById('totalBruto').textContent = `R$ ${totalBruto.toFixed(2)}`;
    document.getElementById('totalLiquido').textContent = `R$ ${totalLiquido.toFixed(2)}`;
    
    if (desconto > 0) {
        document.getElementById('descontoValor').textContent = `- R$ ${(totalBruto * desconto / 100).toFixed(2)}`;
        document.getElementById('descontoInfo').style.display = 'block';
    } else {
        document.getElementById('descontoInfo').style.display = 'none';
    }
}