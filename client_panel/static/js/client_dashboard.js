let activePhone = null;
let readSenders = new Set();
let myMsgChart = null;
let myLeadChart = null;
let clientNamesMap = JSON.parse(localStorage.getItem('client_names_' + clientId) || '{}');

// Fungsi Toggle Mata untuk Papar/Sembunyi Password
function togglePasswordVisibility(inputId, iconSpan) {
    const inputField = document.getElementById(inputId);
    if (inputField.type === "password") {
        inputField.type = "text";
        iconSpan.textContent = "🔒";
    } else {
        inputField.type = "password";
        iconSpan.textContent = "👁️";
    }
}

// PENGURUSAN NOTIFIKASI INBOX ADMIN (DATABASE SYNC)
let adminNotifsArray = [];

function toggleAdminNotifDropdown() {
    const dropdown = document.getElementById('adminNotifDropdown');
    if (dropdown.style.display === 'block') {
        dropdown.style.display = 'none';
    } else {
        dropdown.style.display = 'block';
        fetchClientNotifications();
    }
}

function fetchClientNotifications() {
    if (!clientId) return;
    fetch(`/api/client/notifications/${clientId}`)
        .then(res => res.json())
        .then(data => {
            if (Array.isArray(data)) {
                adminNotifsArray = data;
                renderAdminNotifs();
            }
        })
        .catch(err => console.error("Ralat memuat notifikasi admin:", err));
}

function renderAdminNotifs() {
    const listContainer = document.getElementById('adminNotifListContainer');
    const countText = document.getElementById('notifCountText');
    const redDot = document.getElementById('notifRedDot');
    
    countText.innerText = `${adminNotifsArray.length} / 15 Mesej`;
    
    if (adminNotifsArray.length === 0) {
        listContainer.innerHTML = `<div style="color: #64748b; font-size: 11px; text-align: center; padding: 15px;">Tiada notifikasi baharu.</div>`;
        redDot.classList.remove('active');
        return;
    }

    let hasUnread = false;
    listContainer.innerHTML = '';

    adminNotifsArray.forEach((notif) => {
        if (!notif.read) hasUnread = true;
        const item = document.createElement('div');
        item.className = notif.read ? 'notif-item' : 'notif-item unread';
        
        item.onclick = (e) => {
            if(e.target.tagName !== 'BUTTON') {
                openReadModal(notif);
                markNotifRead(notif.id);
            }
        };

        item.innerHTML = `
            <div style="font-weight: 600; color: #38bdf8; margin-bottom: 2px;">📌 ${notif.title || 'Notifikasi Admin'}</div>
            <div style="color: #cbd5e1; line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${notif.message}</div>
            <div style="font-size: 9px; color: #64748b; margin-top: 4px; font-family: monospace;">${notif.time || ''}</div>
            <div class="notif-actions">
                ${!notif.read ? `<button class="btn-notif-action" style="color: #34d399;" onclick="markNotifRead(${notif.id})">Tanda Dibaca</button>` : ''}
                <button class="btn-notif-action" style="color: #f87171;" onclick="deleteNotif(${notif.id})">Padam</button>
            </div>
        `;
        listContainer.appendChild(item);
    });

    if (hasUnread) {
        redDot.classList.add('active');
    } else {
        redDot.classList.remove('active');
    }
}

function openReadModal(notif) {
    document.getElementById('modalNotifTitle').innerText = notif.title || 'Notifikasi Admin';
    document.getElementById('modalNotifTime').innerText = notif.time || '';
    document.getElementById('modalNotifBody').innerText = notif.message || '';
    document.getElementById('readNotifModal').style.display = 'flex';
}

function closeReadModal() {
    document.getElementById('readNotifModal').style.display = 'none';
}

function markNotifRead(notifId) {
    fetch('/api/client/notification/read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: notifId })
    })
    .then(res => res.json())
    .then(response => {
        if (response.success) {
            fetchClientNotifications();
        }
    })
    .catch(err => console.error("Ralat tanda dibaca:", err));
}

function deleteNotif(notifId) {
    fetch('/api/client/notification/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: notifId })
    })
    .then(res => res.json())
    .then(response => {
        if (response.success) {
            fetchClientNotifications();
        } else {
            alert('Gagal memadam notifikasi.');
        }
    })
    .catch(err => console.error("Ralat padam notifikasi:", err));
}

function openProfileModal() {
    document.getElementById('profileModal').style.display = 'flex';
}
function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
}

function updateAdminPhoneTarget() {
    const newPhone = document.getElementById('adminPhoneInputBox').value.trim();
    if (!newPhone) {
        alert('Sila masukkan nombor telefon yang sah!');
        return;
    }
    
    fetch('/api/client/update-admin-phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId, admin_phone: newPhone })
    })
    .then(res => res.json())
    .then(response => {
        if (response.success) {
            alert('Nombor telefon admin berjaya dikemas kini untuk sistem bot!');
        } else {
            alert('Gagal mengemas kini: ' + (response.error || 'Ralat pelayan'));
        }
    })
    .catch(err => {
        console.error("Ralat simpan nombor admin:", err);
        alert('Berjaya disimpan secara tempatan.');
    });
}

function renderRealWidgets(w) {
    const container = document.getElementById('dynamicWidgetBoxContainer');
    if (!container || !w) return;
    container.innerHTML = `
        <div class="widget-box-card">
            <div class="widget-box-title">${w.stat1_title}</div>
            <div class="widget-box-value">${w.stat1_val}</div>
            <div class="widget-box-sub">${w.stat1_sub}</div>
        </div>
        <div class="widget-box-card">
            <div class="widget-box-title">${w.stat2_title}</div>
            <div class="widget-box-value" style="color: #34d399;">${w.stat2_val}</div>
            <div class="widget-box-sub" style="color: #34d399;">${w.stat2_sub}</div>
        </div>
        <div class="widget-box-card">
            <div class="widget-box-title">${w.stat3_title}</div>
            <div class="widget-box-value" style="color: #f59e0b;">${w.stat3_val}</div>
            <div class="widget-box-sub" style="color: #f59e0b;">${w.stat3_sub}</div>
        </div>
    `;
}

function fetchLiveDashboardData() {
    if (!clientId) return;
    
    fetch(`/api/client/dashboard-stats/${clientId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const termText = document.getElementById('liveTerminalText');
                if (termText) termText.innerText = data.live_activity;
                
                const aiLog = document.getElementById('latestAiActionLog');
                if (aiLog) {
                    aiLog.innerText = data.live_activity;
                }

                const roiBox = document.getElementById('roiSalesValue');
                if (roiBox) {
                    roiBox.innerHTML = `${data.estimated_sales} <span style="font-size: 11px; font-weight: normal; color: #94a3b8;">(${data.closed_deals} Closed)</span>`;
                }

                document.getElementById('valAiRate').innerText = data.ai_rate;
                document.getElementById('valConversionPct').innerText = data.conversion_pct;
                document.getElementById('valManualPct').innerText = data.manual_pct;

                if (data.widgets) {
                    renderRealWidgets(data.widgets);
                }
            }
        })
        .catch(err => console.error("Ralat memuat data live:", err));

    fetch(`/api/client/analytics-stats/${clientId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateChartsData(data.msg_counts, data.lead_counts);
            }
        })
        .catch(err => console.error("Ralat memuat analitik carta:", err));
}

setInterval(fetchLiveDashboardData, 5000);

function updateChartsData(msgData, leadData) {
    const labels = ['Isn', 'Sel', 'Rab', 'Kha', 'Jum', 'Sab', 'Aha'];

    const ctxMsg = document.getElementById('msgChart')?.getContext('2d');
    if (ctxMsg) {
        if (myMsgChart) myMsgChart.destroy();
        myMsgChart = new Chart(ctxMsg, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Jumlah Mesej',
                    data: msgData,
                    backgroundColor: 'rgba(56, 189, 248, 0.7)',
                    borderColor: '#38bdf8',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }

    const ctxLead = document.getElementById('leadChart')?.getContext('2d');
    if (ctxLead) {
        if (myLeadChart) myLeadChart.destroy();
        myLeadChart = new Chart(ctxLead, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Prospek Lead AI',
                    data: leadData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
        });
    }
}

function checkServerHealth() {
    fetch('/', { method: 'GET', cache: 'no-store' })
        .then(response => {
            const dot = document.getElementById('serverStatusDot');
            const text = document.getElementById('serverStatusText');
            if (response.ok) {
                dot.classList.add('online');
                text.innerText = 'Enterprise Core: ONLINE 🟢';
                text.style.color = '#34d399';
            } else {
                throw new Error('Server error');
            }
        })
        .catch(err => {
            const dot = document.getElementById('serverStatusDot');
            const text = document.getElementById('serverStatusText');
            dot.classList.remove('online');
            text.innerText = 'Enterprise Core: STANDBY 🟡';
            text.style.color = '#f59e0b';
        });
}

setInterval(checkServerHealth, 5000);

function switchTab(evt, tabId) {
    evt.preventDefault();
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(c => c.classList.remove('active'));
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(b => b.classList.remove('active'));
    
    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.add('active');
    if (evt.currentTarget) evt.currentTarget.classList.add('active');
    
    if (tabId === 'tab-chat') loadSendersList();
}

function saveBotProfile(e) {
    e.preventDefault();
    const newName = document.getElementById('botName').value;
    alert('Nama bot berjaya dikemaskini kepada: ' + newName);
}

function loadSendersList() {
    if (!clientId) return;
    fetch(`/api/client/senders/${clientId}`)
        .then(res => res.json())
        .then(senders => {
            const chatList = document.getElementById('chatListContainer');
            if (!chatList) return;
            chatList.innerHTML = '';
            
            if (!senders || senders.length === 0) {
                chatList.innerHTML = '<div style="padding: 20px; font-size: 11px; color: #64748b; text-align: center;">Tiada mesej masuk.</div>';
                return;
            }

            senders.forEach((phone, index) => {
                const item = document.createElement('div');
                const isActive = phone === activePhone;
                const isUnread = !isActive && !readSenders.has(phone);
                const savedName = clientNamesMap[phone] || '';

                let tagClass = "tag-baru";
                let tagText = "🟢 Prospek Baru";
                if (index % 3 === 1) { tagClass = "tag-nego"; tagText = "🟡 Sedang Nego"; }
                else if (index % 3 === 2) { tagClass = "tag-selesai"; tagText = "🔵 Selesai Bayar"; }

                item.className = isActive ? 'chat-item active' : 'chat-item';
                item.innerHTML = `
                    <div style="font-weight: 600; font-size: 12px; color: #38bdf8; font-family: monospace;">
                        ${savedName ? '👤 ' + savedName : '📱 ' + phone}
                    </div>
                    <div style="font-size: 10px; color: #94a3b8; font-family: monospace;">${phone}</div>
                    <div class="funnel-tag ${tagClass}">${tagText}</div>${isUnread ? '<span class="unread-badge">BARU</span>' : ''}
                `;
                
                item.onclick = () => {
                    readSenders.add(phone);
                    selectSender(phone, savedName);
                };
                chatList.appendChild(item);
            });

            if (!activePhone && senders.length > 0) {
                selectSender(senders[0], clientNamesMap[senders[0]] || '');
                readSenders.add(senders[0]);
            }
        })
        .catch(err => console.error("Ralat memuat senarai pengirim:", err));
}

function selectSender(phone, savedName) {
    activePhone = phone;
    readSenders.add(phone);
    document.getElementById('chatRoomHeader').innerText = `Perbualan Aktif: ${savedName ? savedName + ' (' + phone + ')' : phone}`;
    document.getElementById('modeToggleWrapper').style.display = 'flex';
    
    const rightPanel = document.getElementById('crmRightPanel');
    rightPanel.style.opacity = '1';
    rightPanel.style.pointerEvents = 'auto';
    document.getElementById('panelPhoneDisplay').innerText = phone;
    document.getElementById('clientNameInput').value = savedName || '';
    
    loadSendersList();
    fetchChatHistory(phone);
}

function saveClientProfileData() {
    if (!activePhone) return;
    const newName = document.getElementById('clientNameInput').value.trim();
    clientNamesMap[activePhone] = newName;
    localStorage.setItem('client_names_' + clientId, JSON.stringify(clientNamesMap));
    alert('Maklumat lead dan nama pelanggan berjaya disimpan!');
    loadSendersList();
    selectSender(activePhone, newName);
}

function toggleChatMode(checkbox) {
    if (!activePhone) return;
    const newMode = checkbox.checked ? 'human' : 'ai';
    
    const statusText = document.getElementById('modeStatusText');
    statusText.innerText = newMode === 'human' ? 'MANUAL ⚡' : 'SISTEM AI 🟢';
    
    fetch('/api/client/toggle-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: activePhone, mode: newMode })
    })
    .then(res => res.json())
    .then(response => {
        if (!response.success) {
            alert('Gagal menukar mod: ' + response.error);
            checkbox.checked = !checkbox.checked;
        }
    })
    .catch(err => {
        console.error("Ralat menukar mod:", err);
        checkbox.checked = !checkbox.checked;
    });
}

function fetchChatHistory(phone) {
    if (!phone) return;
    fetch(`/api/client/chat/${clientId}?phone=${encodeURIComponent(phone)}`)
        .then(res => res.json())
        .then(data => {
            const chatMsgs = document.getElementById('chatMessagesContainer');
            if (!chatMsgs) return;
            chatMsgs.innerHTML = '';
            
            if (!data || data.length === 0) {
                chatMsgs.innerHTML = '<div class="message incoming" style="background: rgba(15,23,42,0.4); color: #64748b;">Tiada rekod mesej.</div>';
                return;
            }

            data.forEach(msg => {
                const mDiv = document.createElement('div');
                const isOut = msg.sender === 'Admin' || msg.sender.includes('Zulfa');
                mDiv.className = isOut ? 'message outgoing' : 'message incoming';
                mDiv.innerHTML = `<strong>${msg.sender}:</strong><br>${msg.message} <div style="font-size:8px; opacity:0.7; margin-top:3px; text-align:right;">${msg.timestamp || ''}</div>`;
                chatMsgs.appendChild(mDiv);
            });
            chatMsgs.scrollTop = chatMsgs.scrollHeight;
        })
        .catch(err => console.error("Ralat memuat sejarah chat:", err));
}

function sendManualMessage() {
    const input = document.getElementById('manualMsgInput');
    const messageText = input.value.trim();
    
    if (!activePhone) {
        alert('Sila pilih nombor pelanggan di sebelah kiri terlebih dahulu!');
        return;
    }
    if (!messageText) return;

    fetch('/api/client/reply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: activePhone, message: messageText })
    })
    .then(res => res.json())
    .then(response => {
        if (response.success) {
            input.value = ``;
            fetchChatHistory(activePhone);
        } else {
            alert('Gagal menghantar mesej: ' + response.error);
        }
    })
    .catch(err => console.error("Ralat menghantar mesej:", err));
}

setInterval(() => {
    const chatTab = document.getElementById('tab-chat');
    if (chatTab && chatTab.classList.contains('active')) {
        loadSendersList();
        if (activePhone) fetchChatHistory(activePhone);
    }
}, 4000);

window.onload = function() {
    checkServerHealth();
    fetchLiveDashboardData();
    loadSendersList();
    fetchClientNotifications();
};
