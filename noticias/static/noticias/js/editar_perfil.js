/* ============================================================
   MODAL — Informações do anonimato
============================================================ */

const modal = document.getElementById("infoModal");
const openBtn = document.getElementById("openInfo");
const closeBtn = document.getElementById("closeInfo");

// Abre modal ao clicar no ícone
if (openBtn) {
    openBtn.addEventListener("click", () => {
        modal.style.display = "flex";
    });
}

// Fecha modal ao clicar no botão X
if (closeBtn) {
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });
}

// Fecha ao clicar fora da caixa
window.addEventListener("click", e => {
    if (e.target === modal) {
        modal.style.display = "none";
    }
});


/* ============================================================
   DESTAQUE EM PREFERÊNCIAS FUTURAS
============================================================ */

const prefs = document.querySelectorAll(".pref-item");

prefs.forEach(item => {
    item.addEventListener("click", () => {
        item.classList.toggle("active");
    });
});


/* ============================================================
   INTERAÇÃO DOS CAMPOS (focus/blur)
============================================================ */

const inputs = document.querySelectorAll(".input-box");

inputs.forEach(input => {
    input.addEventListener("focus", () => {
        input.style.border = "1px solid #888";
    });
    input.addEventListener("blur", () => {
        input.style.border = "1px solid #ddd";
    });
});


/* ============================================================
   PREVIEW DA FOTO DO PERFIL
============================================================ */

const fotoInput = document.getElementById("fotoInput");
const fotoPreview = document.getElementById("photoPreview");

if (fotoInput) {
    fotoInput.addEventListener("change", event => {
        const file = event.target.files[0];
        if (file) {
            fotoPreview.src = URL.createObjectURL(file);
        }
    });
}


/* ============================================================
   MENSAGEM DE SUCESSO (opcional – Django messages)
============================================================ */

const popupSuccess = document.getElementById("successMessage");

if (popupSuccess) {
    setTimeout(() => {
        popupSuccess.style.opacity = "0";
    }, 4000);
}


/* ============================================================
   SISTEMA DE ABAS FUTURO (caso queira usar depois)
============================================================ */

const tabs = document.querySelectorAll("[data-tab]");
const tabAreas = document.querySelectorAll(".tab-area");

tabs.forEach(tab => {
    tab.addEventListener("click", () => {
        const alvo = tab.dataset.tab;

        // ativa aba clicada
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        // mostra conteúdo correspondente
        tabAreas.forEach(area => {
            area.style.display = area.id === alvo ? "block" : "none";
        });
    });
});
