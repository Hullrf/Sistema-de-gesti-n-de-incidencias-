document.addEventListener('DOMContentLoaded', function () {
  var url = '/dashboard/api/stats';
  if (typeof filterUserId !== 'undefined' && filterUserId) {
    url += '?user_id=' + filterUserId;
  }

  fetch(url)
    .then(function (res) { return res.json(); })
    .then(function (data) {
      var colors = ['#ffc107', '#0d6efd', '#198754'];

      document.getElementById('total-count').textContent = data.total;
      document.getElementById('pendiente-count').textContent = data.data[0];
      document.getElementById('enproceso-count').textContent = data.data[1];
      document.getElementById('resuelto-count').textContent = data.data[2];

      new Chart(document.getElementById('barChart'), {
        type: 'bar',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Incidencias',
            data: data.data,
            backgroundColor: colors,
            borderRadius: 6,
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
      });

      new Chart(document.getElementById('pieChart'), {
        type: 'pie',
        data: {
          labels: data.labels,
          datasets: [{
            data: data.data,
            backgroundColor: colors,
            hoverOffset: 8,
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom' } }
        }
      });
    })
    .catch(function (err) {
      console.error('Error cargando estadísticas:', err);
    });
});
