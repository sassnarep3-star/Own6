document.querySelectorAll('input[data-filter]').forEach(function(inp){
  var t=document.getElementById(inp.dataset.filter);
  inp.addEventListener('input',function(){var q=inp.value.toLowerCase();
    t.querySelectorAll('tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)<0?'none':''});});
});
document.querySelectorAll('table.sortable th').forEach(function(th,i){
  th.addEventListener('click',function(){var tb=th.closest('table').tBodies[0];var rows=[].slice.call(tb.rows);
    var dir=th.dataset.dir=th.dataset.dir==='1'?'-1':'1';
    rows.sort(function(a,b){var x=a.cells[i].textContent.trim(),y=b.cells[i].textContent.trim();
      var nx=parseFloat(x),ny=parseFloat(y);var c=(!isNaN(nx)&&!isNaN(ny))?nx-ny:x.localeCompare(y);return c*dir});
    rows.forEach(function(r){tb.appendChild(r)});});
});
