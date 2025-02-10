// Global variables
window.lastFetchedHistoryData = null;
window.currentHistoryHours = 1;
window.currentView = "table";
window.historicalDataVisible = false;

// Fetches the most recent sensor data
function updateData() {
  fetch('/latest')
    .then(response => response.json())
    .then(data => {
      document.getElementById('temp').innerText = data.temp || "--";
      document.getElementById('hum').innerText = data.hum || "--";

      // Flashes a green dot whenever new data is fetched
      const statusDot = document.getElementById('status-dot');
      statusDot.classList.add('flash');
      setTimeout(() => {
        statusDot.classList.remove('flash');
      }, 150);
    })
    .catch(error => console.error('Error fetching data:', error));
}

// Fetches historical data and updates the UI if the history view is visible
function fetchHistory(hours) {
  window.currentHistoryHours = hours;
  
  fetch(`/history?hours=${hours}`)
    .then(response => response.json())
    .then(data => {
      // Save the data globally
      window.lastFetchedHistoryData = data;
      // Updates the UI if historical view is visible
      if (window.historicalDataVisible) {
        if (window.currentView === "graph") {
          updateGraph(data);
        } else {
          updateTable(data);
        }
      }
    })
    .catch(error => console.error("History fetching error:", error));
}

// Sets historical data to visible and fetches new historical data
function showHistory(hours) {
  window.historicalDataVisible = true;
  fetchHistory(hours);
}

// Updates the table with historical data
function updateTable(data) {
  const tableContainer = document.getElementById('table-container');
  const tableBody = document.getElementById('data-table-body');
  const dataControls = document.getElementById('data-controls');
  const graphContainer = document.getElementById('graph-container');
  const toggleBtn = document.getElementById('show-graph');

  // Populates the table
  tableBody.innerHTML = "";
  data.forEach(entry => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${entry.datetime}</td>
      <td>${entry.temperature}°C</td>
      <td>${entry.humidity}%</td>
    `;
    tableBody.appendChild(row);
  });

  // Shows the table view and the data display controls; hides the graph
  tableContainer.style.display = "block";
  graphContainer.style.display = "none";
  dataControls.style.display = "flex";
  toggleBtn.innerText = "Pokaż wykres";
  window.currentView = "table";
}

// Updates (or creates) the graph with historical data
function updateGraph(data) {
  const tableContainer = document.getElementById('table-container');
  const graphContainer = document.getElementById('graph-container');
  const canvas = document.getElementById('data-chart');
  const dataControls = document.getElementById('data-controls');
  const toggleBtn = document.getElementById('show-graph');

  // Shows the graph view and the controls; hides the table.
  tableContainer.style.display = "none";
  graphContainer.style.display = "block";
  dataControls.style.display = "flex";
  toggleBtn.innerText = "Pokaż tabelę";

  // Adjusts canvas size
  const containerWidth = graphContainer.clientWidth;
  const containerHeight = graphContainer.clientHeight;
  canvas.width = containerWidth * window.devicePixelRatio;
  canvas.height = containerHeight * window.devicePixelRatio;
  canvas.style.width = '100%';
  canvas.style.height = '100%';

  const ctx = canvas.getContext('2d');

  // Reverses the data so that the oldest entries are on the left
  const labels = data.map(entry => entry.datetime).reverse();
  const tempData = data.map(entry => entry.temperature).reverse();
  const humData = data.map(entry => entry.humidity).reverse();

  if (window.myChart) {
    window.myChart.data.labels = labels;
    window.myChart.data.datasets[0].data = tempData;
    window.myChart.data.datasets[1].data = humData;
    window.myChart.update();
  } else {
    window.myChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Temperatura (°C)',
            data: tempData,
            borderColor: '#FF6384',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            fill: false,
            tension: 0.1
          },
          {
            label: 'Wilgotność (%)',
            data: humData,
            borderColor: '#36A2EB',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            fill: false,
            tension: 0.1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: { display: true }
          },
          y: {
            beginAtZero: true,
            suggestedMin: 0,
            suggestedMax: 100,
            title: { display: true }
          }
        }
      }
    });
  }
  window.currentView = "graph";
}

// Hides the historical data view and control buttons
function hideDataDisplay() {
  document.getElementById('table-container').style.display = "none";
  document.getElementById('graph-container').style.display = "none";
  document.getElementById('data-controls').style.display = "none";
  window.historicalDataVisible = false;
}

// Adds event listeners once the document is loaded
document.addEventListener("DOMContentLoaded", function() {
  const toggleBtn = document.getElementById("show-graph");
  const tableContainer = document.getElementById('table-container');
  const graphContainer = document.getElementById('graph-container');

  // Toggles between table and graph views
  toggleBtn.addEventListener("click", function() {
    if (window.currentView === "table") {
      window.currentView = "graph";
      tableContainer.style.display = "none";
      graphContainer.style.display = "block";
      toggleBtn.innerText = "Pokaż tabelę";
      window.historicalDataVisible = true;
      if (window.lastFetchedHistoryData) {
        updateGraph(window.lastFetchedHistoryData);
      }
    } else {
      window.currentView = "table";
      graphContainer.style.display = "none";
      tableContainer.style.display = "block";
      toggleBtn.innerText = "Pokaż wykres";
      window.historicalDataVisible = true;
      if (window.lastFetchedHistoryData) {
        updateTable(window.lastFetchedHistoryData);
      }
    }
  });

  // Event listener for the "hide data" button
  document.getElementById("hide-data").addEventListener("click", function() {
    hideDataDisplay();
  });

  // Automatically refreshes historical data every minute (if historicalDataVisible is true)
  setInterval(function() {
    if (window.historicalDataVisible) {
      fetchHistory(window.currentHistoryHours);
    } else {
      fetch(`/history?hours=${window.currentHistoryHours}`)
        .then(response => response.json())
        .then(data => {
          window.lastFetchedHistoryData = data;
        })
        .catch(error => console.error("Historical data fetching error:", error));
    }
  }, 60000);
});

// Refreshes the sensor data view every second.
setInterval(updateData, 1000);
window.onload = updateData;
