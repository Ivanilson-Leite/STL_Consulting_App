/**
 * STL Consulting - Gerenciador de Alertas Globais
 * Uso: STLAlert.success('Titulo', 'Mensagem');
 */

const STLAlert = {
    modalId: 'stlGlobalModal',

    // Configuração dos tipos
    types: {
        success: {
            icon: 'fa-check-circle',
            class: 'stl-type-success',
            defaultTitle: 'Sucesso!'
        },
        error: {
            icon: 'fa-times-circle',
            class: 'stl-type-error',
            defaultTitle: 'Ops! Algo deu errado.'
        },
        warning: {
            icon: 'fa-exclamation-circle',
            class: 'stl-type-warning',
            defaultTitle: 'Atenção'
        },
        info: {
            icon: 'fa-info-circle',
            class: 'stl-type-info',
            defaultTitle: 'Informação'
        }
    },

    // Função Principal para exibir
    show: function(type, message, title = null) {
        const modalEl = document.getElementById(this.modalId);
        if (!modalEl) {
            console.error('STLAlert: Modal HTML não encontrado na página.');
            return;
        }

        const config = this.types[type] || this.types.info;
        const modalTitle = title || config.defaultTitle;

        // 1. Limpa classes antigas do modal-content (para resetar cor)
        const modalContent = modalEl.querySelector('.modal-content');
        modalContent.className = 'modal-content border-0 shadow-lg overflow-hidden';
        modalContent.classList.add(config.class);

        // 2. Define o Ícone
        const iconContainer = document.getElementById('stlModalIcon');
        iconContainer.innerHTML = `<i class="fa ${config.icon} stl-alert-icon"></i>`;

        // 3. Define Textos
        document.getElementById('stlModalTitle').innerText = modalTitle;
        document.getElementById('stlModalMessage').innerHTML = message; // innerHTML permite negrito se precisar

        // 4. Exibe o Modal usando Bootstrap 5
        const bsModal = new bootstrap.Modal(modalEl);
        bsModal.show();
    },

    // Atalhos rápidos
    success: function(message, title) { this.show('success', message, title); },
    error:   function(message, title) { this.show('error', message, title); },
    warning: function(message, title) { this.show('warning', message, title); },
    info:    function(message, title) { this.show('info', message, title); }
};
