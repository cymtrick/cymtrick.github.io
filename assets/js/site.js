/* Progressive enhancement only: the page is complete without this file. */
(function () {
  'use strict';

  /* ── Table of contents from h2 headings ─────────────────────── */
  var toc = document.querySelector('[data-toc]');
  var body = document.querySelector('.post-body');
  if (toc && body) {
    var heads = Array.prototype.slice.call(body.querySelectorAll('h2'));
    heads = heads.filter(function (h) { return !h.closest('.refs'); });
    if (heads.length < 2) {
      toc.parentNode.style.display = 'none';
    } else {
      var links = heads.map(function (h) {
        if (!h.id) h.id = h.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = '#' + h.id; a.textContent = h.textContent;
        li.appendChild(a); toc.appendChild(li);
        return a;
      });
      if ('IntersectionObserver' in window) {
        var current = null;
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) {
              current = e.target;
              links.forEach(function (a, i) { a.classList.toggle('active', heads[i] === current); });
            }
          });
        }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });
        heads.forEach(function (h) { io.observe(h); });
      }
    }
  }

  /* ── Link bracketed citations [n] to the reference list ─────── */
  if (body) {
    var refs = body.querySelector('.refs');
    if (refs) {
      var items = refs.querySelectorAll('ol > li');
      items.forEach(function (li, i) { if (!li.id) li.id = 'ref-' + (i + 1); });
      var n = items.length;
      var walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT, {
        acceptNode: function (node) {
          var p = node.parentNode;
          if (!p || p.closest('.refs, pre, code, .math, svg, a')) return NodeFilter.FILTER_REJECT;
          return /\[\d{1,2}(?:\s*[,–-]\s*\d{1,2})*\]/.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
        }
      });
      var nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(function (node) {
        var frag = document.createDocumentFragment();
        var re = /\[(\d{1,2}(?:\s*[,–-]\s*\d{1,2})*)\]/g;
        var text = node.nodeValue, last = 0, m;
        while ((m = re.exec(text))) {
          frag.appendChild(document.createTextNode(text.slice(last, m.index).replace(/\s+$/, '')));
          var parts = m[1].split(/\s*,\s*/);
          var span = document.createElement('span');
          span.className = 'cite';
          parts.forEach(function (part, k) {
            var range = part.split(/\s*[–-]\s*/);
            var a = document.createElement('a');
            var first = parseInt(range[0], 10);
            a.href = '#ref-' + first;
            a.textContent = part;
            a.className = 'cite';
            if (first > n) a.removeAttribute('href');
            span.appendChild(a);
            if (k < parts.length - 1) span.appendChild(document.createTextNode(','));
          });
          frag.appendChild(span);
          last = m.index + m[0].length;
        }
        frag.appendChild(document.createTextNode(text.slice(last)));
        node.parentNode.replaceChild(frag, node);
      });
    }
  }

  /* ── Chart tooltips: any element with data-tip inside .fig-frame ── */
  var frames = document.querySelectorAll('.fig-frame');
  frames.forEach(function (frame) {
    var targets = frame.querySelectorAll('[data-tip]');
    if (!targets.length) return;
    var tip = document.createElement('div');
    tip.className = 'chart-tip';
    frame.appendChild(tip);
    function show(el) {
      tip.innerHTML = el.getAttribute('data-tip');
      var fr = frame.getBoundingClientRect();
      var r = el.getBoundingClientRect();
      var ax = el.getAttribute('data-ax');
      var x = r.left + r.width / 2 - fr.left;
      var y = (ax === 'top' ? r.top : r.top) - fr.top;
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
      tip.classList.add('show');
    }
    function hide() { tip.classList.remove('show'); }
    targets.forEach(function (el) {
      el.addEventListener('mouseenter', function () { show(el); });
      el.addEventListener('mouseleave', hide);
      el.addEventListener('focus', function () { show(el); });
      el.addEventListener('blur', hide);
      el.setAttribute('tabindex', '0');
    });
  });
})();
