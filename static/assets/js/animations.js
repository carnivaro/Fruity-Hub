/* ===================================================
   FRUITY HUB
   LIVELY ANIMATIONS — scroll reveals + cart bump
   Pure progressive enhancement: safe to remove any time.
=================================================== */

(function () {

    var prefersReducedMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ==========================
       AUTO-TAG ELEMENTS FOR SCROLL REVEAL
       (keeps templates untouched — selectors match
       classes already used across the site)
    ========================== */

    var groupSelectors = [
        '.category-grid > *',
        '.product-grid > *',
        '.values-grid > *',
        '.trust-grid > *',
        '.feature-list > *',
        '.contact-list > *',
        '.orders-list > *'
    ];

    var singleSelectors = [
        '.section-heading',
        '.summary-card',
        '.form-card',
        '.profile-card',
        '.auth-card',
        '.empty-state'
    ];

    var sideLeftSelectors = ['.detail-image', '.about-image'];
    var sideRightSelectors = ['.detail-copy', '.about-copy', '.contact-info'];

    function tagGroup(selector) {
        var groups = document.querySelectorAll(selector);

        // stagger children within each shared parent
        var counters = new Map();
        groups.forEach(function (el) {
            var parent = el.parentElement;
            var count = counters.get(parent) || 0;
            el.classList.add('reveal');
            el.style.setProperty('--reveal-delay', Math.min(count * 0.08, 0.4) + 's');
            counters.set(parent, count + 1);
        });
    }

    function tagSingle(selector) {
        document.querySelectorAll(selector).forEach(function (el) {
            el.classList.add('reveal');
        });
    }

    groupSelectors.forEach(tagGroup);
    singleSelectors.forEach(tagSingle);

    sideLeftSelectors.forEach(function (selector) {
        document.querySelectorAll(selector).forEach(function (el) {
            el.classList.add('reveal', 'reveal-left');
        });
    });

    sideRightSelectors.forEach(function (selector) {
        document.querySelectorAll(selector).forEach(function (el) {
            el.classList.add('reveal', 'reveal-right');
        });
    });

    /* ==========================
       INTERSECTION OBSERVER
    ========================== */

    var revealTargets = document.querySelectorAll('.reveal');

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
        revealTargets.forEach(function (el) { el.classList.add('is-visible'); });
    } else {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

        revealTargets.forEach(function (el) { observer.observe(el); });
    }

    /* ==========================
       CART BADGE BUMP
       Watches the cart count badge (already used by
       cart.js) and gives the basket icon a little bounce
       whenever the number changes.
    ========================== */

    document.addEventListener('DOMContentLoaded', function () {
        var badge = document.getElementById('cartCount');
        var cartLink = document.querySelector('.cart-link');
        if (!badge || !cartLink) return;

        var lastValue = badge.textContent;

        var badgeObserver = new MutationObserver(function () {
            if (badge.textContent !== lastValue) {
                lastValue = badge.textContent;
                cartLink.classList.remove('bump');
                // force reflow so the animation can restart
                void cartLink.offsetWidth;
                cartLink.classList.add('bump');
            }
        });

        badgeObserver.observe(badge, { childList: true, characterData: true, subtree: true });
    });

}());
