(() => {
    const validThemes = new Set(['ocean', 'aurora', 'ember', 'forest', 'rose', 'graphite']);

    function currentTheme() {
        return validThemes.has(document.documentElement.dataset.theme)
            ? document.documentElement.dataset.theme
            : 'ocean';
    }

    function applyTheme(theme) {
        if (!validThemes.has(theme)) return;
        document.documentElement.dataset.theme = theme;
        try { localStorage.setItem('adm-theme', theme); } catch (_) {}
        document.querySelectorAll('[data-theme-option]').forEach((button) => {
            button.setAttribute('aria-checked', String(button.dataset.themeOption === theme));
        });
    }

    function closeThemeMenu() {
        const menu = document.getElementById('theme-menu');
        const toggle = document.getElementById('theme-toggle');
        if (!menu || !toggle) return;
        menu.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
    }

    function initializeSettings(root = document) {
        root.querySelectorAll('[data-controls]').forEach((input) => {
            const controlled = document.getElementById(input.dataset.controls);
            if (controlled) controlled.classList.toggle('hidden', !input.checked);
        });
        const frequency = root.querySelector('[data-schedule-select]');
        if (frequency) updateScheduleFields(frequency.value);
    }

    function updateScheduleFields(frequency) {
        const weekly = document.getElementById('discord-weekday-wrapper');
        const monthly = document.getElementById('discord-monthday-wrapper');
        if (weekly) weekly.classList.toggle('hidden', frequency !== 'weekly');
        if (monthly) monthly.classList.toggle('hidden', frequency !== 'monthly');
    }

    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(currentTheme());
        initializeSettings();

        const toggle = document.getElementById('theme-toggle');
        const menu = document.getElementById('theme-menu');
        if (toggle && menu) {
            toggle.addEventListener('click', (event) => {
                event.stopPropagation();
                menu.hidden = !menu.hidden;
                toggle.setAttribute('aria-expanded', String(!menu.hidden));
            });
        }
    });

    document.addEventListener('click', (event) => {
        const themeOption = event.target.closest('[data-theme-option]');
        if (themeOption) {
            applyTheme(themeOption.dataset.themeOption);
            closeThemeMenu();
            return;
        }

        const navTarget = event.target.closest('[data-nav]');
        if (navTarget) {
            document.querySelectorAll('.nav-link').forEach((link) => link.classList.remove('is-active'));
            const matchingNav = document.querySelector(`.nav-link[data-nav="${navTarget.dataset.nav}"]`);
            if (matchingNav) matchingNav.classList.add('is-active');
        }

        if (!event.target.closest('.theme-picker')) closeThemeMenu();
    });

    document.addEventListener('change', (event) => {
        if (event.target.matches('[data-controls]')) {
            const controlled = document.getElementById(event.target.dataset.controls);
            if (controlled) controlled.classList.toggle('hidden', !event.target.checked);
        }
        if (event.target.matches('[data-schedule-select]')) updateScheduleFields(event.target.value);
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeThemeMenu();
    });

    document.addEventListener('htmx:afterSwap', (event) => initializeSettings(event.target));
})();
