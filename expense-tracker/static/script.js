document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('expense-form');
  const descriptionInput = document.getElementById('description');
  const amountInput = document.getElementById('amount');
  const dateInput = document.getElementById('date');
  const tbody = document.querySelector('#expenses-table tbody');

  let dailyChart, monthlyChart, yearlyChart;

  function fetchExpenses() {
    fetch('/api/expenses')
      .then(res => res.json())
      .then(data => {
        tbody.innerHTML = '';
        data.forEach(exp => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${exp.description}</td>
            <td>${exp.amount.toFixed(2)}</td>
            <td>${exp.date}</td>
            <td><button class="action-btn" data-id="${exp.id}">Delete</button></td>
          `;
          tbody.appendChild(tr);
        });
      });
  }

  function fetchSummary() {
    fetch('/api/summary')
      .then(res => res.json())
      .then(data => {
        updateChart(dailyChart, 'Daily Expenses', data.daily.map(e => e.date).reverse(), data.daily.map(e => e.total).reverse());
        updateChart(monthlyChart, 'Monthly Expenses', data.monthly.map(e => e.month).reverse(), data.monthly.map(e => e.total).reverse());
        updateChart(yearlyChart, 'Yearly Expenses', data.yearly.map(e => e.year).reverse(), data.yearly.map(e => e.total).reverse());
      });
  }

  function updateChart(chart, label, labels, data) {
    if (!chart) return;
    chart.data.labels = labels;
    chart.data.datasets[0].label = label;
    chart.data.datasets[0].data = data;
    chart.update();
  }

  form.addEventListener('submit', e => {
    e.preventDefault();
    const payload = {
      description: descriptionInput.value,
      amount: parseFloat(amountInput.value),
      date: dateInput.value
    };
    fetch('/api/expenses', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(() => {
      form.reset();
      fetchExpenses();
      fetchSummary();
    });
  });

  tbody.addEventListener('click', e => {
    if (e.target.classList.contains('action-btn')) {
      const id = e.target.dataset.id;
      fetch('/api/expenses/' + id, {method: 'DELETE'})
      .then(res => res.json())
      .then(() => {
        fetchExpenses();
        fetchSummary();
      });
    }
  });

  const ctxDaily = document.getElementById('dailyChart').getContext('2d');
  dailyChart = new Chart(ctxDaily, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Daily',
        data: [],
        borderColor: 'rgba(0,123,255,0.7)',
        fill: false,
        tension: 0.1
      }]
    },
    options: { responsive: true }
  });

  const ctxMonthly = document.getElementById('monthlyChart').getContext('2d');
  monthlyChart = new Chart(ctxMonthly, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Monthly',
        data: [],
        borderColor: 'rgba(0,123,255,0.7)',
        fill: false,
        tension: 0.1
      }]
    },
    options: { responsive: true }
  });

  const ctxYearly = document.getElementById('yearlyChart').getContext('2d');
  yearlyChart = new Chart(ctxYearly, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Yearly',
        data: [],
        borderColor: 'rgba(0,123,255,0.7)',
        fill: false,
        tension: 0.1
      }]
    },
    options: { responsive: true }
  });

  fetchExpenses();
  fetchSummary();
});
