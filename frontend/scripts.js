document.addEventListener('DOMContentLoaded', function() {
    const monthSelect = document.getElementById('month-select');
    const searchBox = document.getElementById('search-box');
    const transactionsTableBody = document.getElementById('transactions-table-body');
    const totalSaleAmount = document.getElementById('total-sale-amount');
    const totalSoldItems = document.getElementById('total-sold-items');
    const totalNotSoldItems = document.getElementById('total-not-sold-items');
    const prevPageButton = document.getElementById('prev-page');
    const nextPageButton = document.getElementById('next-page');
    const barChartCtx = document.getElementById('bar-chart').getContext('2d');
    
    let currentPage = 1;
    let currentMonth = '03';
    let searchQuery = '';

    const fetchTransactions = () => {
        fetch(`/transactions?month=${currentMonth}&search=${searchQuery}&page=${currentPage}`)
            .then(response => response.json())
            .then(data => {
                transactionsTableBody.innerHTML = '';
                data.forEach(transaction => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${transaction.title}</td>
                        <td>${transaction.description}</td>
                        <td>${transaction.price}</td>
                        <td>${transaction.date_of_sale}</td>
                        <td>${transaction.category}</td>
                        <td>${transaction.sold ? 'Yes' : 'No'}</td>
                    `;
                    transactionsTableBody.appendChild(row);
                });
            });
    };

    const fetchStatistics = () => {
        fetch(`/statistics?month=${currentMonth}`)
            .then(response => response.json())
            .then(data => {
                totalSaleAmount.textContent = `Total Sale Amount: ${data.total_sale_amount}`;
                totalSoldItems.textContent = `Total Sold Items: ${data.total_sold_items}`;
                totalNotSoldItems.textContent = `Total Not Sold Items: ${data.total_not_sold_items}`;
            });
    };

    const fetchBarChartData = () => {
        fetch(`/bar-chart?month=${currentMonth}`)
            .then(response => response.json())
            .then(data => {
                const labels = data.map(item => item.price_range);
                const counts = data.map(item => item.count);
                new Chart(barChartCtx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Number of Items',
                            data: counts,
                            backgroundColor: 'rgba(0, 123, 255, 0.5)',
                            borderColor: 'rgba(0, 123, 255, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    };

    monthSelect.addEventListener('change', () => {
        currentMonth = monthSelect.value;
        currentPage = 1;
        fetchTransactions();
        fetchStatistics();
        fetchBarChartData();
    });

    searchBox.addEventListener('input', () => {
        searchQuery = searchBox.value;
        currentPage = 1;
        fetchTransactions();
    });

    prevPageButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            fetchTransactions();
        }
    });

    nextPageButton.addEventListener('click', () => {
        currentPage++;
        fetchTransactions();
    });

    
    fetchTransactions();
    fetchStatistics();
    fetchBarChartData();
});
