/**
 * Formatação de números no padrão brasileiro (milhar com ponto, decimais com vírgula).
 * Classes: .money-br (2 casas), .dec-br-2 / .dec-br-3 / .dec-br-4, .int-br (inteiro).
 */
(function (global) {
  'use strict';

  function onlyNumChars(s) {
    return String(s || '')
      .replace(/[^\d.,\-]/g, '')
      .replace('-', '');
  }

  function parseToNumber(s) {
    s = onlyNumChars(s);
    if (!s) return NaN;
    if (s.indexOf(',') >= 0) {
      s = s.replace(/\./g, '').replace(',', '.');
    } else if ((s.match(/\./g) || []).length > 1) {
      s = s.replace(/\./g, '');
    }
    return parseFloat(s);
  }

  function formatBR(num, fracDigits) {
    if (num === null || num === undefined || isNaN(num)) return '';
    var parts = Number(num).toFixed(fracDigits).split('.');
    var intp = parts[0];
    var frac = parts[1];
    intp = intp.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return intp + ',' + frac;
  }

  function bindOnce(inp, fn) {
    if (inp.dataset && inp.dataset.brInputsBound === '1') return;
    fn(inp);
    if (inp.dataset) inp.dataset.brInputsBound = '1';
  }

  function bindMoneyBr(root) {
    root.querySelectorAll(
      'input.money-br:not([readonly]):not(.maintenance-total-readonly):not(.fuel-total-readonly)'
    ).forEach(function (inp) {
      bindOnce(inp, function (el) {
        el.addEventListener('blur', function () {
          var n = parseToNumber(el.value);
          if (!isNaN(n)) el.value = formatBR(n, 2);
        });
        el.addEventListener('focus', function () {
          el.select();
        });
      });
    });
  }

  function bindDecBr(root, className, places) {
    root.querySelectorAll('input.' + className).forEach(function (inp) {
      if (inp.readOnly) return;
      bindOnce(inp, function (el) {
        el.addEventListener('blur', function () {
          var n = parseToNumber(el.value);
          if (!isNaN(n)) el.value = formatBR(n, places);
        });
        el.addEventListener('focus', function () {
          el.select();
        });
      });
    });
  }

  function bindIntBr(root) {
    root.querySelectorAll('input.int-br').forEach(function (inp) {
      bindOnce(inp, function (el) {
        el.addEventListener('blur', function () {
          var s = String(el.value || '').replace(/\D/g, '');
          el.value = s || '';
        });
        el.addEventListener('focus', function () {
          el.select();
        });
      });
    });
  }

  /** Soma peças + mão de obra nos formulários de manutenção (IDs fixos nos templates). */
  function bindMaintenanceTotals(root) {
    root.querySelectorAll('#maintenance-form, #maintenance-form-edit').forEach(function (form) {
      if (form.dataset && form.dataset.brMaintenanceTotalBound === '1') return;
      var partsInp = form.querySelector('input[name="parts_amount"]');
      var laborInp = form.querySelector('input[name="labor_amount"]');
      var totalInp = form.querySelector('input[name="total_amount"]');
      if (!totalInp) return;

      function recalc() {
        var p = parseToNumber(partsInp && partsInp.value);
        var l = parseToNumber(laborInp && laborInp.value);
        if (isNaN(p)) p = 0;
        if (isNaN(l)) l = 0;
        var sum = p + l;
        var partsEmpty = !partsInp || !String(partsInp.value || '').trim();
        var laborEmpty = !laborInp || !String(laborInp.value || '').trim();
        if (sum === 0 && partsEmpty && laborEmpty) {
          totalInp.value = '';
          return;
        }
        totalInp.value = formatBR(sum, 2);
      }

      [partsInp, laborInp].forEach(function (inp) {
        if (!inp) return;
        inp.addEventListener('input', recalc);
        inp.addEventListener('change', recalc);
        inp.addEventListener('blur', recalc);
      });
      if (form.dataset) form.dataset.brMaintenanceTotalBound = '1';
      recalc();
    });
  }

  /** Total = litros × preço nos formulários de combustível (IDs fixos nos templates). */
  function bindFuelTotals(root) {
    root.querySelectorAll('#fuel-form, #fuel-form-edit').forEach(function (form) {
      if (form.dataset && form.dataset.brFuelTotalBound === '1') return;
      var litersInp = form.querySelector('input[name="liters"]');
      var priceInp = form.querySelector('input[name="price_per_liter"]');
      var totalInp = form.querySelector('input[name="total_amount"]');
      if (!totalInp) return;

      function recalc() {
        var L = parseToNumber(litersInp && litersInp.value);
        var P = parseToNumber(priceInp && priceInp.value);
        if (isNaN(L) || isNaN(P)) {
          totalInp.value = '';
          return;
        }
        totalInp.value = formatBR(L * P, 2);
      }

      [litersInp, priceInp].forEach(function (inp) {
        if (!inp) return;
        inp.addEventListener('input', recalc);
        inp.addEventListener('change', recalc);
        inp.addEventListener('blur', recalc);
      });
      if (form.dataset) form.dataset.brFuelTotalBound = '1';
      recalc();
    });
  }

  function init(root) {
    root = root || document;
    bindMoneyBr(root);
    bindDecBr(root, 'dec-br-2', 2);
    bindDecBr(root, 'dec-br-3', 3);
    bindDecBr(root, 'dec-br-4', 4);
    bindIntBr(root);
    bindMaintenanceTotals(root);
    bindFuelTotals(root);
  }

  global.BRInputs = {
    init: init,
    parseToNumber: parseToNumber,
    formatBR: formatBR,
  };

  document.addEventListener('DOMContentLoaded', function () {
    init(document);
  });
})(typeof window !== 'undefined' ? window : this);
