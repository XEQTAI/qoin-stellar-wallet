// QOIN Wallet Frontend - Comic Book Edition! 💥

// Configuration
const API_URL = https://qoin-stellar-wallet.onrender.com; // Replace with your deployed API URL
const API_KEY = rnd_PoRW2WCEuK2Q8mrab2qtatbOA03C; // Replace with your API key

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_URL}${endpoint}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Request failed');
        }

        return { success: true, data: result };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Show/hide result boxes
function showResult(elementId, content, isSuccess = true) {
    const resultBox = document.getElementById(elementId);
    resultBox.innerHTML = content;
    resultBox.className = `result-box ${isSuccess ? 'success' : 'error'}`;
    resultBox.classList.remove('hidden');

    // Add sound effect text
    const soundEffect = document.createElement('div');
    soundEffect.style.cssText = `
        position: absolute;
        top: -30px;
        right: 10px;
        font-family: 'Bangers', cursive;
        font-size: 2rem;
        color: ${isSuccess ? '#00FF00' : '#FF0000'};
        text-shadow: 2px 2px 0 #000;
        animation: popIn 0.5s ease;
    `;
    soundEffect.textContent = isSuccess ? 'POW!' : 'OUCH!';
    resultBox.style.position = 'relative';
    resultBox.appendChild(soundEffect);

    setTimeout(() => soundEffect.remove(), 1000);
}

// Create Wallet
document.getElementById('createWalletForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const userId = document.getElementById('userId').value;
    const email = document.getElementById('userEmail').value;

    showResult('createResult', '<div class="loading"></div> Creating your superhero wallet...', true);

    const result = await apiCall('/api/wallet/create', 'POST', {
        user_id: userId,
        email: email
    });

    if (result.success) {
        const data = result.data;
        showResult('createResult', `
            <h3>🎉 WALLET CREATED! 🎉</h3>
            <p><strong>Wallet Address:</strong></p>
            <code>${data.wallet_address}</code>
            <p><strong>⚠️ SECRET KEY (Save this!):</strong></p>
            <code>${data.secret_key}</code>
            <p style="color: red; font-weight: bold;">
                Save your secret key NOW! You'll need it to send Qoins!
            </p>
        `, true);
    } else {
        showResult('createResult', `
            <h3>❌ ERROR!</h3>
            <p>${result.error}</p>
        `, false);
    }
});

// Deposit
document.getElementById('depositForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const address = document.getElementById('depositAddress').value;
    const amount = parseFloat(document.getElementById('depositAmount').value);

    showResult('depositResult', '<div class="loading"></div> Minting Qoins...', true);

    const result = await apiCall('/api/deposit', 'POST', {
        wallet_address: address,
        amount: amount
    });

    if (result.success) {
        const data = result.data;
        showResult('depositResult', `
            <h3>💰 QOINS MINTED! 💰</h3>
            <p><strong>Amount Minted:</strong> ${data.amount_minted} QOIN</p>
            <p><strong>New Balance:</strong> ${data.new_balance} QOIN</p>
            <p><strong>Transaction Hash:</strong></p>
            <code>${data.tx_hash}</code>
        `, true);
    } else {
        showResult('depositResult', `
            <h3>❌ ERROR!</h3>
            <p>${result.error}</p>
        `, false);
    }
});

// Send
document.getElementById('sendForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fromAddress = document.getElementById('sendFrom').value;
    const toAddress = document.getElementById('sendTo').value;
    const amount = parseFloat(document.getElementById('sendAmount').value);
    const secretKey = document.getElementById('sendSecret').value;

    const fee = (amount * 0.01).toFixed(7);
    const netAmount = (amount - fee).toFixed(7);

    showResult('sendResult', '<div class="loading"></div> Sending Qoins...', true);

    const result = await apiCall('/api/send', 'POST', {
        from_address: fromAddress,
        to_address: toAddress,
        amount: amount,
        secret_key: secretKey
    });

    if (result.success) {
        const data = result.data;
        showResult('sendResult', `
            <h3>🚀 QOINS SENT! 🚀</h3>
            <p><strong>Amount Sent:</strong> ${data.amount_sent} QOIN</p>
            <p><strong>Fee (1%):</strong> ${data.fee_charged} QOIN</p>
            <p><strong>Your New Balance:</strong> ${data.new_balance} QOIN</p>
            <p><strong>Transaction Hash:</strong></p>
            <code>${data.tx_hash}</code>
        `, true);
    } else {
        showResult('sendResult', `
            <h3>❌ ERROR!</h3>
            <p>${result.error}</p>
        `, false);
    }
});

// Check Balance
document.getElementById('balanceForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const address = document.getElementById('balanceAddress').value;

    showResult('balanceResult', '<div class="loading"></div> Checking power level...', true);

    const result = await apiCall(`/api/balance/${address}`, 'GET');

    if (result.success) {
        const data = result.data;
        showResult('balanceResult', `
            <h3>🔍 BALANCE CHECK! 🔍</h3>
            <p><strong>Wallet Address:</strong></p>
            <code>${data.wallet_address}</code>
            <p><strong>Database Balance:</strong> ${data.balance_db} QOIN</p>
            <p><strong>Stellar Balance:</strong> ${data.balance_stellar} QOIN</p>
            <p style="font-size: 2rem; text-align: center; margin: 1rem 0;">
                💰 ${data.balance_db} QOIN 💰
            </p>
        `, true);
    } else {
        showResult('balanceResult', `
            <h3>❌ ERROR!</h3>
            <p>${result.error}</p>
        `, false);
    }
});

// Easter egg: Add comic sound effects on form submit
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', (e) => {
        const sounds = ['BAM!', 'POW!', 'ZAP!', 'BOOM!', 'KAPOW!'];
        const sound = sounds[Math.floor(Math.random() * sounds.length)];

        const soundEl = document.createElement('div');
        soundEl.textContent = sound;
        soundEl.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-family: 'Bangers', cursive;
            font-size: 5rem;
            color: #FFD700;
            -webkit-text-stroke: 3px #000;
            z-index: 9999;
            animation: explode 0.8s ease-out forwards;
            pointer-events: none;
        `;

        document.body.appendChild(soundEl);
        setTimeout(() => soundEl.remove(), 800);
    });
});

// Add CSS animation for explosion
const style = document.createElement('style');
style.textContent = `
    @keyframes explode {
        0% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(0);
        }
        50% {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1.5);
        }
        100% {
            opacity: 0;
            transform: translate(-50%, -50%) scale(2);
        }
    }

    @keyframes popIn {
        0% {
            opacity: 0;
            transform: scale(0);
        }
        50% {
            transform: scale(1.2);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }
`;
document.head.appendChild(style);

console.log('🦸‍♂️ QOIN Wallet loaded! Ready to save the crypto world! 🦸‍♀️');
