// Fetch API Data
async function fetchData() {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) throw new Error('Failed to fetch data');

        const data = await response.json();
        document.getElementById('temperature').innerText = data.temperature;
        document.getElementById('humidity').innerText = data.humidity;
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Update data setiap 5 detik
setInterval(fetchData, 5000);
fetchData();