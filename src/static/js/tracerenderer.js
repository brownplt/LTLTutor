/**
 * TraceRenderer — Custom SVG trace diagram renderer for LTL Tutor.
 *
 * Renders a horizontal sequence of state boxes connected by arrows,
 * with an optional curved back-edge arc for cycle states.
 *
 * Usage:
 *   TraceRenderer.render(containerElement, {
 *     prefix: [{ label: "¬c  ¬e  q" }, ...],
 *     cycle:  [{ label: "c  ¬e  ¬q" }, ...]
 *   }, { highlightIndex: 3 });
 */
var TraceRenderer = (function () {
    'use strict';

    var NS = 'http://www.w3.org/2000/svg';
    var _counter = 0;

    function _uid() {
        return 'trc' + (++_counter);
    }

    function _el(tag, attrs) {
        var el = document.createElementNS(NS, tag);
        if (attrs) {
            for (var k in attrs) {
                if (attrs.hasOwnProperty(k)) {
                    el.setAttribute(k, attrs[k]);
                }
            }
        }
        return el;
    }

    // Shared canvas for text measurement
    var _measureCanvas = null;
    function _textWidth(text, font) {
        if (!_measureCanvas) {
            _measureCanvas = document.createElement('canvas');
        }
        var ctx = _measureCanvas.getContext('2d');
        ctx.font = font;
        return ctx.measureText(text).width;
    }

    var CFG = {
        font: '13px SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
        padX: 14,
        padY: 10,
        boxH: 38,
        gap: 44,
        gapMin: 24,
        arrowLen: 7,
        radius: 6,
        marginX: 16,
        marginY: 16,
        prefixFill: '#ffffff',
        cycleFill: '#f0f4f8',
        stroke: '#aaa',
        strokeW: 1.5,
        hlStroke: '#333',
        hlWidth: 3,
        arrowFill: '#666',
        textFill: '#212529',
        arcMinD: 28,
        arcFactor: 0.06,
        arcMaxD: 56,
        minBoxW: 52,
        lineH: 18,
        verticalThreshold: 800
    };

    /**
     * @param {HTMLElement} container  DOM element to render into (contents replaced).
     * @param {Object}      traceData  { prefix: [{label}], cycle: [{label}] }
     * @param {Object}      [options]  { highlightIndex: number|null }
     */
    function render(container, traceData, options) {
        options = options || {};
        var hlIdx = (options.highlightIndex != null) ? options.highlightIndex : -1;
        var prefix = traceData.prefix || [];
        var cycle = traceData.cycle || [];

        if (!prefix.length && !cycle.length) {
            container.innerHTML = '<p class="text-muted small">No trace data.</p>';
            return;
        }

        var id = _uid();

        // Build unified state list
        var states = [];
        var i, j;
        for (i = 0; i < prefix.length; i++) {
            states.push({ label: prefix[i].label, isCycle: false, gi: i });
        }
        for (i = 0; i < cycle.length; i++) {
            states.push({ label: cycle[i].label, isCycle: true, gi: prefix.length + i });
        }

        // Split labels into per-variable arrays
        var maxVars = 1;
        for (i = 0; i < states.length; i++) {
            states[i].vars = states[i].label.split('\u2003');
            if (states[i].vars.length > maxVars) maxVars = states[i].vars.length;
        }

        // Measure inline widths (all vars on one line)
        var totalInlineW = CFG.marginX * 2 + Math.max(0, states.length - 1) * CFG.gap;
        for (i = 0; i < states.length; i++) {
            var tw = _textWidth(states[i].label, CFG.font);
            states[i].inlineW = Math.max(Math.ceil(tw) + CFG.padX * 2, CFG.minBoxW);
            totalInlineW += states[i].inlineW;
        }

        // Decide layout: stack vars vertically if inline is too wide and multiple vars exist
        var useVertical = (maxVars > 1) && (totalInlineW > CFG.verticalThreshold);

        var boxH;
        if (useVertical) {
            boxH = CFG.padY * 2 + CFG.lineH * maxVars;
            for (i = 0; i < states.length; i++) {
                var maxVarW = 0;
                for (j = 0; j < states[i].vars.length; j++) {
                    var vw = _textWidth(states[i].vars[j].trim(), CFG.font);
                    if (vw > maxVarW) maxVarW = vw;
                }
                states[i].w = Math.max(Math.ceil(maxVarW) + CFG.padX * 2, CFG.minBoxW);
            }
        } else {
            boxH = CFG.boxH;
            for (i = 0; i < states.length; i++) {
                states[i].w = states[i].inlineW;
            }
        }

        // Compress gaps for wide traces to fit better
        var totalW = CFG.marginX * 2;
        for (i = 0; i < states.length; i++) totalW += states[i].w;
        totalW += Math.max(0, states.length - 1) * CFG.gap;
        var gap = CFG.gap;
        if (totalW > CFG.verticalThreshold && states.length > 2) {
            gap = Math.max(CFG.gapMin, CFG.gap - Math.floor((totalW - CFG.verticalThreshold) / (states.length - 1)));
        }

        // Horizontal layout
        var x = CFG.marginX;
        var y = CFG.marginY;
        for (i = 0; i < states.length; i++) {
            states[i].x = x;
            states[i].y = y;
            x += states[i].w + gap;
        }
        var svgW = x - gap + CFG.marginX;

        // Compute back-edge arc depth
        var arcD = 0;
        if (cycle.length > 0) {
            var fci = prefix.length;           // first cycle index in states[]
            var lci = states.length - 1;       // last cycle index
            if (cycle.length === 1) {
                arcD = 36;
            } else {
                var hd = (states[lci].x + states[lci].w / 2)
                       - (states[fci].x + states[fci].w / 2);
                arcD = Math.min(CFG.arcMaxD, CFG.arcMinD + hd * CFG.arcFactor);
            }
        }

        var svgH = y + boxH + (arcD > 0 ? arcD + 14 : 0) + CFG.marginY;

        // --- Build SVG ---
        var svg = _el('svg', {
            'viewBox': '0 0 ' + svgW + ' ' + svgH,
            'width': '100%',
            'role': 'img',
            'aria-label': 'Trace diagram with ' + states.length + ' states'
        });
        svg.style.maxWidth = svgW + 'px';
        svg.style.display = 'block';

        // Defs — arrowhead marker
        var defs = _el('defs', {});
        var mkId = id + '-ah';
        var mk = _el('marker', {
            'id': mkId,
            'markerWidth': String(CFG.arrowLen),
            'markerHeight': String(CFG.arrowLen),
            'refX': String(CFG.arrowLen),
            'refY': String(CFG.arrowLen / 2),
            'orient': 'auto',
            'markerUnits': 'userSpaceOnUse'
        });
        mk.appendChild(_el('polygon', {
            'points': '0 0,' + CFG.arrowLen + ' ' + (CFG.arrowLen / 2) + ',0 ' + CFG.arrowLen,
            'fill': CFG.arrowFill
        }));
        defs.appendChild(mk);
        svg.appendChild(defs);

        // --- State boxes ---
        for (i = 0; i < states.length; i++) {
            var s = states[i];
            var hl = (s.gi === hlIdx);
            var g = _el('g', {});

            g.appendChild(_el('rect', {
                'x': s.x, 'y': s.y,
                'width': s.w, 'height': boxH,
                'rx': CFG.radius, 'ry': CFG.radius,
                'fill': s.isCycle ? CFG.cycleFill : CFG.prefixFill,
                'stroke': hl ? CFG.hlStroke : CFG.stroke,
                'stroke-width': hl ? CFG.hlWidth : CFG.strokeW
            }));

            if (useVertical && s.vars.length > 1) {
                // Vertical layout: one variable per line
                var totalTextH = CFG.lineH * s.vars.length;
                var startY = s.y + (boxH - totalTextH) / 2 + CFG.lineH / 2;
                for (var vi = 0; vi < s.vars.length; vi++) {
                    var varTxt = _el('text', {
                        'x': s.x + s.w / 2,
                        'y': startY + vi * CFG.lineH,
                        'text-anchor': 'middle',
                        'dominant-baseline': 'central',
                        'fill': CFG.textFill,
                        'font-family': 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                        'font-size': '13'
                    });
                    varTxt.textContent = s.vars[vi].trim();
                    g.appendChild(varTxt);
                }
            } else {
                var txt = _el('text', {
                    'x': s.x + s.w / 2,
                    'y': s.y + boxH / 2,
                    'text-anchor': 'middle',
                    'dominant-baseline': 'central',
                    'fill': CFG.textFill,
                    'font-family': 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                    'font-size': '13'
                });
                txt.textContent = s.label;
                g.appendChild(txt);
            }

            svg.appendChild(g);
        }

        // --- Forward arrows ---
        for (i = 0; i < states.length - 1; i++) {
            var from = states[i], to = states[i + 1];
            svg.appendChild(_el('line', {
                'x1': from.x + from.w,
                'y1': from.y + boxH / 2,
                'x2': to.x,
                'y2': to.y + boxH / 2,
                'stroke': CFG.arrowFill,
                'stroke-width': '1.5',
                'marker-end': 'url(#' + mkId + ')'
            }));
        }

        // --- Cycle back-edge ---
        if (cycle.length > 0) {
            var fc = states[prefix.length];     // first cycle state
            var lc = states[states.length - 1]; // last cycle state

            if (cycle.length === 1) {
                // Self-loop arc below the single cycle state
                var scx = fc.x + fc.w / 2;
                var scy = fc.y + boxH;
                svg.appendChild(_el('path', {
                    'd': 'M ' + (scx - 12) + ' ' + scy +
                         ' C ' + (scx - 12) + ' ' + (scy + arcD) +
                         ', ' + (scx + 12) + ' ' + (scy + arcD) +
                         ', ' + (scx + 12) + ' ' + scy,
                    'fill': 'none',
                    'stroke': CFG.arrowFill,
                    'stroke-width': '1.5',
                    'marker-end': 'url(#' + mkId + ')'
                }));
            } else {
                // Arc from bottom of last cycle state back to bottom of first cycle state
                var sx = lc.x + lc.w / 2;
                var sy = lc.y + boxH;
                var ex = fc.x + fc.w / 2;
                var ey = fc.y + boxH;
                var ctrlY = sy + arcD;

                svg.appendChild(_el('path', {
                    'd': 'M ' + sx + ' ' + sy +
                         ' C ' + sx + ' ' + ctrlY +
                         ', ' + ex + ' ' + ctrlY +
                         ', ' + ex + ' ' + ey,
                    'fill': 'none',
                    'stroke': CFG.arrowFill,
                    'stroke-width': '1.5',
                    'marker-end': 'url(#' + mkId + ')'
                }));
            }
        }

        container.innerHTML = '';
        container.appendChild(svg);
    }

    return { render: render };
})();
