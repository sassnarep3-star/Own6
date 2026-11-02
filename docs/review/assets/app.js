/* Own6 independent review — progressive enhancement only, no external deps. */
(function () {
  'use strict';
  document.querySelectorAll('a[target="_blank"]').forEach(function (a) {
    if (!a.getAttribute('rel')) a.setAttribute('rel', 'noopener');
  });
  document.querySelectorAll('input.filter').forEach(function (input) {
    var table = document.getElementById(input.getAttribute('data-target'));
    if (!table) return;
    var body = table.tBodies[0];
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      Array.prototype.forEach.call(body.rows, function (row) {
        row.style.display = row.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
      });
    });
  });
  document.querySelectorAll('table thead th').forEach(function (th, index) {
    th.addEventListener('click', function () {
      var table = th.closest('table'), body = table.tBodies[0];
      var rows = Array.prototype.slice.call(body.rows);
      var asc = th.dataset.asc !== '1';
      th.dataset.asc = asc ? '1' : '0';
      rows.sort(function (a, b) {
        var x = (a.cells[index] || {}).textContent || '';
        var y = (b.cells[index] || {}).textContent || '';
        var nx = parseFloat(x.replace(/[^0-9.\-]/g, '')), ny = parseFloat(y.replace(/[^0-9.\-]/g, ''));
        if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
        return asc ? x.localeCompare(y) : y.localeCompare(x);
      });
      rows.forEach(function (r) { body.appendChild(r); });
    });
  });
}());
