async function loadDashboard() {
    try {
        const response = await fetch('stock_data.json');
        const data = await response.json();

        document.getElementById('update-time').innerText = `Update: ${data.last_updated}`;
        const container = document.getElementById('dashboard');

        data.stocks.forEach(stock => {
            // 외인 또는 기관 3일 연속 매수 시 Hot 카드 설정
            const isHot = stock.consecutive.foreign >= 3 || stock.consecutive.institution >= 3;
            
            // 카드 엘리먼트 생성 (a 태그를 사용하여 클릭 시 이동하도록 설정)
            const card = document.createElement('a');
            card.className = `card ${isHot ? 'hot' : ''}`;
            
            // 요청하신 네이버 증권 차트 URL 구조 적용
            card.href = `https://m.stock.naver.com/fchart/domestic/stock/${stock.symbol}`;
            card.target = "_blank"; // 새 탭에서 열기

            const returnClass = (val) => val > 0 ? 'plus' : (val < 0 ? 'minus' : '');
            const formatPrice = (val) => val.toLocaleString();

            card.innerHTML = `
                <div class="card-header">
                    <div>
                        <div class="stock-name">${stock.name}</div>
                        <div class="stock-symbol">${stock.symbol}</div>
                    </div>
                    <div class="current-price">${formatPrice(stock.price)}원</div>
                </div>

                <div class="returns-grid">
                    <div class="return-item">
                        <label>5일</label>
                        <span class="return-val ${returnClass(stock.returns.R5)}">${stock.returns.R5}%</span>
                    </div>
                    <div class="return-item">
                        <label>10일</label>
                        <span class="return-val ${returnClass(stock.returns.R10)}">${stock.returns.R10}%</span>
                    </div>
                    <div class="return-item">
                        <label>20일</label>
                        <span class="return-val ${returnClass(stock.returns.R20)}">${stock.returns.R20}%</span>
                    </div>
                </div>

                <div class="supply-section">
                    <div class="supply-box foreign-box">
                        <span class="label" style="color: var(--foreign-color)">외국인</span>
                        <span class="consecutive">${stock.consecutive.foreign}일 연속</span>
                        <span class="total-days">(총 ${stock.supply.foreign}일)</span>
                    </div>
                    <div class="supply-box inst-box">
                        <span class="label" style="color: var(--inst-color)">기관</span>
                        <span class="consecutive">${stock.consecutive.institution}일 연속</span>
                        <span class="total-days">(총 ${stock.supply.institution}일)</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });

    } catch (error) {
        console.error("데이터 로드 실패:", error);
        document.getElementById('dashboard').innerHTML = "<p>데이터를 불러올 수 없습니다. JSON 파일 경로를 확인해주세요.</p>";
    }
}

window.onload = loadDashboard;