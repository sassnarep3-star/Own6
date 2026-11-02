// Simple client-side row filter for every table on the site. No external requests.
(function () {
  document.querySelectorAll('input.filter').forEach(function (input) {
    var table = document.getElementById(input.dataset.target);
    if (!table) return;
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      table.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = !q || tr.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
      });
    });
  });
})();
