/**
 * EulerDiagram — Inline SVG Euler diagrams for answer feedback.
 *
 * Draws the set relationship between the traces accepted by the correct
 * answer (solid green) and the student's answer (dashed red), with the
 * actual formulas in a legend and an optional dot marking where the
 * counterexample trace lives.
 *
 * Usage:
 *   EulerDiagram.render(containerElement, 'subsumed', {
 *     correctLabel: 'G(a -> F b)',
 *     yourLabel: 'G(a & F b)',
 *     showTraceDot: true
 *   });
 *
 * Relations: 'disjoint' | 'subsumed' | 'contained' | 'overlap' | 'equivalent'
 *   subsumed  = correct answer subsumes yours (yours is more restrictive)
 *   contained = correct answer is contained in yours (yours is more permissive)
 */
var EulerDiagram = (function () {
    'use strict';

    var NS = 'http://www.w3.org/2000/svg';

    var STYLE = {
        correctStroke: '#198754',
        correctFill: 'rgba(25, 135, 84, 0.14)',
        correctText: '#146c43',
        yourStroke: '#dc3545',
        yourFill: 'rgba(220, 53, 69, 0.14)',
        yourText: '#b02a37',
        dotFill: '#1f2937',
        labelFont: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
    };

    // Each layout: circles in draw order, exclusive-region label anchors,
    // and (for incorrect answers) a spot for the counterexample-trace dot.
    var LAYOUTS = {
        disjoint: {
            circles: [
                { role: 'correct', cx: 125, cy: 120, r: 85 },
                { role: 'yours', cx: 355, cy: 120, r: 85 }
            ],
            correctLabel: { x: 125, y: 120 },
            yourLabel: { x: 355, y: 95 },
            dot: { x: 355, y: 130 },
            desc: 'two separate circles: no trace satisfies both your answer and the correct answer'
        },
        subsumed: {
            circles: [
                { role: 'correct', cx: 240, cy: 125, r: 105 },
                { role: 'yours', cx: 285, cy: 150, r: 55 }
            ],
            correctLabel: { x: 215, y: 60 },
            yourLabel: { x: 285, y: 150 },
            dot: { x: 175, y: 145 },
            desc: 'your answer is a smaller circle entirely inside the correct answer: every trace your answer allows is also allowed by the correct answer, but not vice versa'
        },
        contained: {
            circles: [
                { role: 'yours', cx: 240, cy: 125, r: 105 },
                { role: 'correct', cx: 195, cy: 150, r: 55 }
            ],
            correctLabel: { x: 195, y: 150 },
            yourLabel: { x: 265, y: 60 },
            dot: { x: 295, y: 140 },
            desc: 'the correct answer is a smaller circle entirely inside your answer: your answer allows every trace the correct answer allows, plus extra traces'
        },
        overlap: {
            circles: [
                { role: 'correct', cx: 185, cy: 125, r: 90 },
                { role: 'yours', cx: 295, cy: 125, r: 90 }
            ],
            correctLabel: { x: 148, y: 125 },
            yourLabel: { x: 333, y: 98 },
            dot: { x: 333, y: 133 },
            desc: 'two overlapping circles: your answer and the correct answer share some traces, but each also allows traces the other does not'
        },
        equivalent: {
            circles: [
                { role: 'correct', cx: 240, cy: 125, r: 92 },
                { role: 'yours', cx: 240, cy: 125, r: 80 }
            ],
            correctLabel: { x: 240, y: 110 },
            yourLabel: { x: 240, y: 138 },
            dot: null,
            desc: 'two concentric circles: your answer and the correct answer allow exactly the same traces'
        }
    };

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

    function _escapeHtml(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function _circle(svg, c) {
        var isCorrect = (c.role === 'correct');
        var attrs = {
            'cx': c.cx, 'cy': c.cy, 'r': c.r,
            'fill': isCorrect ? STYLE.correctFill : STYLE.yourFill,
            'stroke': isCorrect ? STYLE.correctStroke : STYLE.yourStroke,
            'stroke-width': 2
        };
        if (!isCorrect) {
            attrs['stroke-dasharray'] = '6 4';
        }
        svg.appendChild(_el('circle', attrs));
    }

    function _label(svg, pos, text, color, opts) {
        opts = opts || {};
        var t = _el('text', {
            'x': pos.x,
            'y': pos.y,
            'text-anchor': 'middle',
            'dominant-baseline': 'central',
            'fill': color,
            'font-family': STYLE.labelFont,
            'font-size': opts.size || '13',
            'font-weight': opts.weight || '600',
            'font-style': opts.italic ? 'italic' : 'normal'
        });
        t.textContent = text;
        svg.appendChild(t);
    }

    /**
     * @param {HTMLElement} container  DOM element to render into (contents replaced).
     * @param {string}      relation   'disjoint'|'subsumed'|'contained'|'overlap'|'equivalent'
     * @param {Object}      [opts]     { correctLabel, yourLabel, showTraceDot }
     */
    function render(container, relation, opts) {
        opts = opts || {};
        var L = LAYOUTS[relation];
        if (!L) {
            container.innerHTML = '';
            return;
        }

        var showDot = !!opts.showTraceDot && !!L.dot;
        var ariaLabel = 'Euler diagram of the traces allowed by each answer: ' + L.desc + '.';
        if (showDot) {
            ariaLabel += ' A dot marks where the counterexample trace shown above falls.';
        }

        var svg = _el('svg', {
            'viewBox': '0 0 480 250',
            'role': 'img',
            'aria-label': ariaLabel
        });
        svg.style.display = 'block';
        svg.style.width = '100%';
        svg.style.height = 'auto';
        svg.style.maxWidth = '420px';

        for (var i = 0; i < L.circles.length; i++) {
            _circle(svg, L.circles[i]);
        }

        _label(svg, L.correctLabel, 'Correct answer', STYLE.correctText);
        _label(svg, L.yourLabel, 'Your answer', STYLE.yourText);

        if (showDot) {
            svg.appendChild(_el('circle', {
                'cx': L.dot.x, 'cy': L.dot.y, 'r': 5,
                'fill': STYLE.dotFill
            }));
            _label(svg, { x: L.dot.x, y: L.dot.y + 18 }, 'trace above', STYLE.dotFill,
                { size: '11', weight: '500', italic: true });
        }

        container.innerHTML = '';
        container.appendChild(svg);

        // Legend with the actual formulas, so the diagram is readable without
        // cross-referencing the option list.
        if (opts.correctLabel || opts.yourLabel) {
            var legend = document.createElement('div');
            legend.className = 'small mt-1';
            var rows = '';
            var swatchBase = 'display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:baseline;';
            if (opts.correctLabel) {
                rows += '<div><span style="' + swatchBase +
                    'background:' + STYLE.correctFill + ';border:2px solid ' + STYLE.correctStroke + ';"></span>' +
                    'Correct answer: <code>' + _escapeHtml(opts.correctLabel) + '</code></div>';
            }
            if (opts.yourLabel) {
                rows += '<div><span style="' + swatchBase +
                    'background:' + STYLE.yourFill + ';border:2px dashed ' + STYLE.yourStroke + ';"></span>' +
                    'Your answer: <code>' + _escapeHtml(opts.yourLabel) + '</code></div>';
            }
            legend.innerHTML = rows;
            container.appendChild(legend);
        }
    }

    return { render: render };
})();
