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

    function _getAvailableWidth(container) {
        var width = 0;
        if (container) {
            width = container.clientWidth || 0;
            if (!width && container.getBoundingClientRect) {
                width = container.getBoundingClientRect().width || 0;
            }
            if (!width && container.parentElement) {
                width = container.parentElement.clientWidth || 0;
            }
        }
        if (!width || !isFinite(width)) {
            return CFG.verticalThreshold;
        }
        return Math.max(320, Math.floor(width));
    }

    function _splitVars(label) {
        var raw = (label || '').trim();
        if (!raw) {
            return [''];
        }

        var parts = raw.split('\u2003');
        if (parts.length === 1) {
            // Fall back to runs of spaces when the em-space separator is unavailable.
            parts = raw.split(/\s{2,}/);
        }

        var vars = [];
        for (var i = 0; i < parts.length; i++) {
            var v = parts[i].trim();
            if (v) {
                vars.push(v);
            }
        }

        return vars.length ? vars : [raw];
    }

    function _isNegatedVar(token) {
        var t = (token || '').trim();
        return t.charAt(0) === '¬' || t.charAt(0) === '!';
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
        hlStroke: '#d97706',
        hlWidth: 4,
        hlFill: '#fff8eb',
        arrowFill: '#666',
        tokenGap: 8,
        tokenLineGap: 5,
        tokenLineH: 18,
        tokenPosText: '#0b4ea2',
        tokenNegText: '#c05f0e',
        indexFont: '11px SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
        indexTextFill: '#667085',
        currentBadgeFill: '#d97706',
        currentBadgeText: '#ffffff',
        currentBadgeH: 16,
        arcMinD: 28,
        arcFactor: 0.06,
        arcMaxD: 56,
        minBoxW: 52,
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
        var availableWidth = _getAvailableWidth(container);

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

        // Split labels into per-variable token metadata
        var maxVars = 1;
        for (i = 0; i < states.length; i++) {
            states[i].vars = _splitVars(states[i].label);
            states[i].tokens = [];
            states[i].inlineTokenW = 0;
            states[i].maxTokenW = 0;
            if (states[i].vars.length > maxVars) maxVars = states[i].vars.length;

            for (j = 0; j < states[i].vars.length; j++) {
                var tokenText = states[i].vars[j];
                var tokenTextW = Math.ceil(_textWidth(tokenText, CFG.font));
                var tokenW = Math.max(tokenTextW, 6);
                var token = {
                    text: tokenText,
                    negated: _isNegatedVar(tokenText),
                    w: tokenW
                };
                states[i].tokens.push(token);
                states[i].inlineTokenW += tokenW;
                if (j < states[i].vars.length - 1) {
                    states[i].inlineTokenW += CFG.tokenGap;
                }
                if (tokenW > states[i].maxTokenW) states[i].maxTokenW = tokenW;
            }
        }

        // Measure inline widths (all vars on one line)
        var totalInlineW = CFG.marginX * 2 + Math.max(0, states.length - 1) * CFG.gap;
        for (i = 0; i < states.length; i++) {
            states[i].inlineW = Math.max(states[i].inlineTokenW + CFG.padX * 2, CFG.minBoxW);
            totalInlineW += states[i].inlineW;
        }

        // Decide layout: stack vars vertically if inline is too wide and multiple vars exist
        var useVertical = (maxVars > 1) && (totalInlineW > availableWidth);

        var boxH;
        if (useVertical) {
            boxH = CFG.padY * 2 + (CFG.tokenLineH * maxVars) + (Math.max(0, maxVars - 1) * CFG.tokenLineGap);
            for (i = 0; i < states.length; i++) {
                states[i].w = Math.max(states[i].maxTokenW + CFG.padX * 2, CFG.minBoxW);
            }
        } else {
            boxH = Math.max(CFG.boxH, CFG.padY * 2 + CFG.tokenLineH);
            for (i = 0; i < states.length; i++) {
                states[i].w = states[i].inlineW;
            }
        }

        // Compress gaps for wide traces to fit better
        var totalW = CFG.marginX * 2;
        for (i = 0; i < states.length; i++) totalW += states[i].w;
        totalW += Math.max(0, states.length - 1) * CFG.gap;
        var gap = CFG.gap;
        if (totalW > availableWidth && states.length > 2) {
            gap = Math.max(CFG.gapMin, CFG.gap - Math.floor((totalW - availableWidth) / (states.length - 1)));
        }

        var showStateIndices = (hlIdx >= 0);
        var topBandH = showStateIndices ? (CFG.currentBadgeH + 10) : 0;

        // Horizontal layout
        var x = CFG.marginX;
        var y = CFG.marginY + topBandH;
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
            'preserveAspectRatio': 'xMinYMin meet',
            'role': 'img',
            'aria-label': 'Trace diagram with ' + states.length + ' states'
        });
        svg.style.display = 'block';
        svg.style.width = '100%';
        svg.style.height = 'auto';
        svg.style.maxWidth = svgW + 'px';

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

        function appendVarToken(group, token, xPos, yPos, textAnchor) {
            var txt = _el('text', {
                'x': xPos,
                'y': yPos + CFG.tokenLineH / 2,
                'text-anchor': textAnchor || 'start',
                'dominant-baseline': 'central',
                'fill': token.negated ? CFG.tokenNegText : CFG.tokenPosText,
                'font-family': 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                'font-size': '13',
                'font-weight': token.negated ? '700' : '500'
            });
            txt.textContent = token.text;
            group.appendChild(txt);
        }

        // --- State boxes ---
        for (i = 0; i < states.length; i++) {
            var s = states[i];
            var hl = (s.gi === hlIdx);
            var g = _el('g', {});
            var stateFill = (hl ? CFG.hlFill : (s.isCycle ? CFG.cycleFill : CFG.prefixFill));

            if (showStateIndices) {
                var idxLabel = _el('text', {
                    'x': s.x + s.w / 2,
                    'y': s.y - 8,
                    'text-anchor': 'middle',
                    'dominant-baseline': 'central',
                    'fill': hl ? CFG.hlStroke : CFG.indexTextFill,
                    'font-family': 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                    'font-size': '11',
                    'font-weight': hl ? '700' : '500'
                });
                idxLabel.textContent = 's' + s.gi;
                g.appendChild(idxLabel);
            }

            g.appendChild(_el('rect', {
                'x': s.x, 'y': s.y,
                'width': s.w, 'height': boxH,
                'rx': CFG.radius, 'ry': CFG.radius,
                'fill': stateFill,
                'stroke': hl ? CFG.hlStroke : CFG.stroke,
                'stroke-width': hl ? CFG.hlWidth : CFG.strokeW
            }));

            if (hl) {
                var badgeText = 'CURRENT';
                var badgeW = Math.max(52, Math.ceil(_textWidth(badgeText, CFG.indexFont)) + 12);
                var badgeX = s.x + (s.w - badgeW) / 2;
                var badgeY = s.y - CFG.currentBadgeH - 2;

                g.appendChild(_el('rect', {
                    'x': badgeX,
                    'y': badgeY,
                    'width': badgeW,
                    'height': CFG.currentBadgeH,
                    'rx': 8,
                    'ry': 8,
                    'fill': CFG.currentBadgeFill
                }));

                var badgeLabel = _el('text', {
                    'x': badgeX + badgeW / 2,
                    'y': badgeY + CFG.currentBadgeH / 2,
                    'text-anchor': 'middle',
                    'dominant-baseline': 'central',
                    'fill': CFG.currentBadgeText,
                    'font-family': 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                    'font-size': '10',
                    'font-weight': '700'
                });
                badgeLabel.textContent = badgeText;
                g.appendChild(badgeLabel);
            }

            if (useVertical && s.tokens.length > 1) {
                var totalTokenH = (s.tokens.length * CFG.tokenLineH) + (Math.max(0, s.tokens.length - 1) * CFG.tokenLineGap);
                var tokenY = s.y + (boxH - totalTokenH) / 2;
                for (var vi = 0; vi < s.tokens.length; vi++) {
                    var vToken = s.tokens[vi];
                    appendVarToken(g, vToken, s.x + s.w / 2, tokenY, 'middle');
                    tokenY += CFG.tokenLineH + CFG.tokenLineGap;
                }
            } else {
                var rowX = s.x + (s.w - s.inlineTokenW) / 2;
                var rowY = s.y + (boxH - CFG.tokenLineH) / 2;
                for (var ti = 0; ti < s.tokens.length; ti++) {
                    var hToken = s.tokens[ti];
                    appendVarToken(g, hToken, rowX, rowY, 'start');
                    rowX += hToken.w + CFG.tokenGap;
                }
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
