// assets/custom_script.js

/**
 * Este script traduz as opções "Select All" e "Deselect All" dos dropdowns do Dash.
 * Como essa tradução não é suportada nativamente, usamos um MutationObserver
 * para interceptar a criação desses elementos na tela e alterar seu texto.
 */

const translateDropdownOptions = () => {
    // Busca por todos os elementos de opção do dropdown
    document.querySelectorAll('.Select-menu-option').forEach(option => {
        if (option.textContent === 'Select All') {
            option.textContent = 'Selecionar Todos';
        } else if (option.textContent === 'Deselect All') {
            option.textContent = 'Remover Todos';
        }
    });
};

// O MutationObserver é a forma mais robusta de detectar quando os menus são abertos.
const observer = new MutationObserver((mutationsList) => {
    for (const mutation of mutationsList) {
        // Verificamos se novos nós (elementos) foram adicionados ao corpo da página
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // Se um menu de dropdown foi adicionado, tentamos a tradução
            const hasDropdownMenu = Array.from(mutation.addedNodes).some(node =>
                node.nodeType === 1 && (node.classList.contains('Select-menu-outer') || node.querySelector('.Select-menu-outer'))
            );
            if (hasDropdownMenu) {
                // Um pequeno atraso para garantir que as opções internas do menu foram renderizadas
                setTimeout(translateDropdownOptions, 50);
            }
        }
    }
});

// Inicia a observação no corpo do documento, monitorando adições de elementos.
observer.observe(document.body, { childList: true, subtree: true });