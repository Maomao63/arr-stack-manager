(() => {
    const validThemes = new Set(['ocean', 'aurora', 'ember', 'forest', 'rose', 'graphite']);
    const requestMethods = ['get', 'post', 'delete'];
    const scheduledLoads = new WeakSet();

    function requestAttribute(element) {
        for (const method of requestMethods) {
            const url = element.getAttribute(`hx-${method}`);
            if (url) return { method: method.toUpperCase(), url };
        }
        return null;
    }

    function appendControl(formData, control) {
        if (!control || !control.name || control.disabled) return;
        if ((control.type === 'checkbox' || control.type === 'radio') && !control.checked) return;
        if (control.tagName === 'SELECT' && control.multiple) {
            Array.from(control.selectedOptions).forEach((option) => formData.append(control.name, option.value));
            return;
        }
        formData.append(control.name, control.value);
    }

    function requestBody(element, method) {
        if (method === 'GET') return undefined;
        const include = element.getAttribute('hx-include');
        if (!include) return undefined;
        if (include === 'closest form') {
            const form = element.closest('form');
            return form ? new FormData(form) : undefined;
        }
        const formData = new FormData();
        document.querySelectorAll(include).forEach((control) => appendControl(formData, control));
        return formData;
    }

    function resolveTarget(element) {
        const selector = element.getAttribute('hx-target');
        if (!selector || selector === 'this') return selector === 'this' ? element : null;
        return document.querySelector(selector);
    }

    function setRequestState(element, active) {
        element.classList.toggle('htmx-request', active);
        const indicatorSelector = element.getAttribute('hx-indicator');
        const indicator = indicatorSelector ? document.querySelector(indicatorSelector) : null;
        if (indicator) indicator.classList.toggle('htmx-request', active);
        if (element.getAttribute('hx-disabled-elt') === 'this') element.disabled = active;
    }

    function swapResponse(element, target, html) {
        const swap = element.getAttribute('hx-swap') || 'innerHTML';
        if (swap === 'outerHTML') {
            target.insertAdjacentHTML('afterend', html);
            const inserted = target.nextElementSibling;
            target.remove();
            if (inserted) initializeDynamicContent(inserted);
        } else {
            target.innerHTML = html;
            initializeDynamicContent(target);
        }
        document.dispatchEvent(new CustomEvent('htmx:afterSwap', { detail: { target } }));
    }

    async function runRequest(element) {
        const request = requestAttribute(element);
        const target = resolveTarget(element);
        if (!request || !target || element.dataset.requestPending === 'true') return;

        const confirmation = element.getAttribute('hx-confirm');
        if (confirmation && !window.confirm(confirmation)) return;

        element.dataset.requestPending = 'true';
        setRequestState(element, true);
        try {
            const response = await fetch(request.url, {
                method: request.method,
                body: requestBody(element, request.method),
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            const responseHtml = await response.text();
            swapResponse(element, target, responseHtml);
        } catch (_) {
            window.alert('The request failed. Check the server connection and try again.');
        } finally {
            delete element.dataset.requestPending;
            setRequestState(element, false);
        }
    }

    function scheduleLoads(root = document) {
        const elements = [];
        if (root.nodeType === Node.ELEMENT_NODE && root.matches('[hx-trigger]')) elements.push(root);
        root.querySelectorAll?.('[hx-trigger]').forEach((element) => elements.push(element));
        elements.forEach((element) => {
            if (scheduledLoads.has(element)) return;
            const trigger = element.getAttribute('hx-trigger') || '';
            if (!/(^|,)\s*load(?:\s|,|$)/.test(trigger)) return;
            scheduledLoads.add(element);
            runRequest(element);
            const intervalMatch = trigger.match(/every\s+(\d+)h/);
            if (intervalMatch) {
                const interval = Number(intervalMatch[1]) * 60 * 60 * 1000;
                window.setInterval(() => {
                    if (element.isConnected) runRequest(element);
                }, interval);
            }
        });
    }

    function initializeDynamicContent(root = document) {
        initializeSettings(root);
        scheduleLoads(root);
    }

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
        initializeDynamicContent();

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
        const requestElement = event.target.closest('[hx-get], [hx-post], [hx-delete]');
        if (requestElement) {
            event.preventDefault();
            runRequest(requestElement);
        }

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

})();
