/**
 * Akıllı Donanım ve Cihaz Seçim Sistemi - KDS Web Arayüzü
 * Karar Destek Sistemleri (MCDM / WSM) Etkileşim ve Veri Yönetim Betiği
 */

// Application State
const state = {
  currentCategory: 'laptop',
  budget: 50000,
  purposes: ['oyun', 'yazilim'],
  weightBands: ['hafif', 'orta', 'agir'],
  budgetTolerance: 0.05,
  devices: [],
  lastEvaluation: null,
  activeTab: 'tab-analysis'
};

// Document Ready
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initCategorySelector();
  initCriteriaListeners();
  initInventoryTab();
  initImportAndReset();
  initLiveSyncControls();
  
  // Initial evaluation on launch
  runEvaluation();
  loadInventory();
  fetchSystemInfo();
  fetchSyncStatusAndHistory();
});

// System Info & Sync Status
async function fetchSystemInfo() {
  try {
    const res = await fetch('/api/info');
    const data = await res.json();
    if (data.status === 'online') {
      const badge = document.getElementById('db-status-badge');
      if (badge) {
        badge.textContent = `SQLite: ${data.database.total_devices} Cihaz Aktif`;
      }
      const invCount = document.getElementById('inventory-tab-count');
      if (invCount) {
        invCount.textContent = data.database.total_devices;
      }

      // Update sync status badges if available
      if (data.last_sync) {
        const syncBadge = document.getElementById('sync-status-badge');
        if (syncBadge) {
          const timeOnly = data.last_sync.synced_at.split(' ')[1] || data.last_sync.synced_at;
          syncBadge.textContent = `Son Güncelleme: ${timeOnly} (${data.last_sync.status})`;
        }
        const methTime = document.getElementById('methodology-last-sync-time');
        if (methTime) methTime.textContent = data.last_sync.synced_at;
        const methStatus = document.getElementById('methodology-last-sync-status');
        if (methStatus) {
          methStatus.textContent = data.last_sync.status;
          methStatus.style.background = data.last_sync.status === 'SUCCESS' ? '#DCFCE7' : '#FEF3C7';
          methStatus.style.color = data.last_sync.status === 'SUCCESS' ? '#15803D' : '#B45309';
        }
        const methSource = document.getElementById('methodology-last-sync-source');
        if (methSource) methSource.textContent = `Kaynak: ${data.last_sync.source}`;
      }
    }
  } catch (err) {
    console.error('System info fetch error:', err);
  }
}

// -------------------------------------------------------------
// 1. TABS MANAGEMENT
// -------------------------------------------------------------
function initTabs() {
  const tabButtons = document.querySelectorAll('.nav-tab-button');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      state.activeTab = targetId;
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }

      if (targetId === 'tab-database') {
        loadInventory();
      }
    });
  });
}

// -------------------------------------------------------------
// 2. CATEGORY SELECTOR & CRITERIA FORM
// -------------------------------------------------------------
function initCategorySelector() {
  const catButtons = document.querySelectorAll('.cat-seg-btn');
  catButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      catButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      state.currentCategory = btn.getAttribute('data-cat');
      updateFormVisibility();
      runEvaluation();
    });
  });
}

function updateFormVisibility() {
  const laptopSection = document.getElementById('laptop-specific-criteria');
  const phoneTabletNotice = document.getElementById('phone-tablet-notice');
  const noticeTitle = document.getElementById('notice-category-title');
  const noticeDesc = document.getElementById('notice-category-desc');

  if (state.currentCategory === 'laptop') {
    if (laptopSection) laptopSection.style.display = 'block';
    if (phoneTabletNotice) phoneTabletNotice.style.display = 'none';
  } else {
    if (laptopSection) laptopSection.style.display = 'none';
    if (phoneTabletNotice) phoneTabletNotice.style.display = 'block';

    if (state.currentCategory === 'phone') {
      noticeTitle.textContent = 'Telefon Değerlendirme Profili';
      noticeDesc.innerHTML = 'KDS Karar Motoru telefon kategorisinde işlemci akıcılığı (<b>cpu_score</b>), kamera kalitesi (<b>camera_score</b>), batarya ömrü (<b>battery_score</b>), ekran kalitesi (<b>display_score</b>) ve bütçe/fiyat verimliliği kıstaslarını otomatik olarak ağırlıklandırmaktadır.';
    } else {
      noticeTitle.textContent = 'Tablet Değerlendirme Profili';
      noticeDesc.innerHTML = 'KDS Karar Motoru tablet kategorisinde ekran/multimedya (<b>display_score</b>), kalem & üretkenlik (<b>camera_or_stylus_score</b>), işlemci gücü (<b>cpu_score</b>), batarya dayanımı (<b>battery_score</b>) ve fiyat verimliliği kıstaslarını otomatik ağırlıklandırmaktadır.';
    }
  }
}

function initCriteriaListeners() {
  // Budget Input
  const budgetInput = document.getElementById('budget-input');
  if (budgetInput) {
    budgetInput.value = state.budget;
    budgetInput.addEventListener('change', (e) => {
      state.budget = Math.max(1000, parseFloat(e.target.value) || 50000);
      runEvaluation();
    });
  }

  // Budget Presets
  const presets = document.querySelectorAll('.budget-preset');
  presets.forEach(p => {
    p.addEventListener('click', () => {
      const val = parseFloat(p.getAttribute('data-val'));
      state.budget = val;
      if (budgetInput) budgetInput.value = val;
      runEvaluation();
    });
  });

  // Tolerance select
  const tolSelect = document.getElementById('budget-tolerance-select');
  if (tolSelect) {
    tolSelect.addEventListener('change', (e) => {
      state.budgetTolerance = parseFloat(e.target.value);
      runEvaluation();
    });
  }

  // Purpose checkboxes (multi-select)
  const purposeBoxes = document.querySelectorAll('input[name="purpose-chk"]');
  purposeBoxes.forEach(chk => {
    chk.addEventListener('change', () => {
      const selected = [];
      purposeBoxes.forEach(cb => {
        if (cb.checked) selected.push(cb.value);
      });
      state.purposes = selected.length > 0 ? selected : ['gunluk'];
      runEvaluation();
    });
  });

  // Weight band checkboxes (multi-select)
  const weightBoxes = document.querySelectorAll('input[name="weight-chk"]');
  weightBoxes.forEach(chk => {
    chk.addEventListener('change', () => {
      const selected = [];
      weightBoxes.forEach(cb => {
        if (cb.checked) selected.push(cb.value);
      });
      state.weightBands = selected.length > 0 ? selected : ['hafif', 'orta', 'agir'];
      runEvaluation();
    });
  });

  // Run button
  const runBtn = document.getElementById('btn-run-evaluation');
  if (runBtn) {
    runBtn.addEventListener('click', runEvaluation);
  }
}

// -------------------------------------------------------------
// 3. RUN KDS DECISION EVALUATION
// -------------------------------------------------------------
async function runEvaluation() {
  const loadingIndicator = document.getElementById('evaluation-loading');
  if (loadingIndicator) loadingIndicator.style.display = 'block';

  try {
    const payload = {
      category: state.currentCategory,
      budget: state.budget,
      purposes: state.purposes,
      weightBands: state.weightBands,
      budget_tolerance: state.budgetTolerance
    };

    const res = await fetch('/api/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.status === 'success') {
      state.lastEvaluation = data.evaluation;
      renderEvaluationResults(data.evaluation);
    }
  } catch (err) {
    console.error('KDS Evaluation failed:', err);
  } finally {
    if (loadingIndicator) loadingIndicator.style.display = 'none';
  }
}

function renderEvaluationResults(evalData) {
  // 1. Executive Summary & Constraints Badges
  const summaryBlock = document.getElementById('kds-summary-block');
  const constraintsContainer = document.getElementById('active-constraints-tags');
  const weightsContainer = document.getElementById('criteria-weights-display');
  const resultsCountText = document.getElementById('results-count-text');

  if (resultsCountText) {
    resultsCountText.innerHTML = `İncelenen Toplam Cihaz: <b>${evalData.total_evaluated}</b> | %60 Barajını Aşan Önerilen: <b style="color:var(--navy-primary);">${evalData.qualified_count}</b> | Elenen: <b style="color:var(--burgundy);">${evalData.eliminated_count}</b>`;
  }

  // Constraints tags
  if (constraintsContainer) {
    constraintsContainer.innerHTML = '';
    evalData.hard_constraints_applied.forEach(c => {
      const tag = document.createElement('span');
      tag.className = 'constraint-tag';
      tag.textContent = c;
      constraintsContainer.appendChild(tag);
    });
  }

  // Dynamic Weights display
  if (weightsContainer && evalData.weights_used) {
    weightsContainer.innerHTML = '';
    const weightLabels = {
      cpu: 'İşlemci (CPU)',
      gpu: 'Grafik (GPU)',
      ram: 'Bellek (RAM)',
      display: 'Ekran',
      battery: 'Batarya',
      portability: 'Taşınabilirlik',
      camera: 'Kamera',
      stylus_or_cam: 'Kalem / Üretkenlik',
      price: 'Fiyat / Bütçe'
    };

    for (const [key, val] of Object.entries(evalData.weights_used)) {
      const item = document.createElement('div');
      item.className = 'weight-item';
      const label = weightLabels[key] || key;
      const pct = (val * 100).toFixed(1);
      item.innerHTML = `<span>${label}:</span> <span class="badge">%${pct}</span>`;
      weightsContainer.appendChild(item);
    }
  }

  // 2. Recommended Devices List (score >= 60%)
  const resultsList = document.getElementById('recommended-results-list');
  resultsList.innerHTML = '';

  if (evalData.recommended.length === 0) {
    resultsList.innerHTML = `
      <div style="background:#FFFDFB; border:1px solid #DCD6CD; padding:32px; text-align:center; border-radius:4px;">
        <h4 style="font-family:var(--font-serif); color:var(--burgundy); margin-bottom:8px;">Kriterlere Uygun Cihaz Bulunamadı</h4>
        <p style="font-size:13.5px; color:var(--text-muted); max-width:540px; margin:0 auto;">
          Belirttiğiniz bütçe (${formatTL(evalData.budget)}) veya seçtiğiniz katı donanım kısıtları (RAM, GPU veya hafiflik) nedeniyle tüm cihazlar elenmiştir. Lütfen bütçeyi artırmayı veya esnek toleransı genişletmeyi deneyiniz.
        </p>
      </div>
    `;
  } else {
    evalData.recommended.forEach((dev, idx) => {
      const card = createDeviceCard(dev, idx + 1);
      resultsList.appendChild(card);
    });
  }

  // 3. Eliminated Devices Section & Table
  const elimTableBody = document.getElementById('eliminated-table-body');
  const elimCountBadge = document.getElementById('eliminated-count-badge');
  const elimWrapper = document.getElementById('eliminated-devices-wrapper');

  if (elimCountBadge) {
    elimCountBadge.textContent = `${evalData.eliminated_count} Cihaz Elendi`;
  }

  if (elimTableBody) {
    elimTableBody.innerHTML = '';
    if (evalData.eliminated.length === 0) {
      elimWrapper.style.display = 'none';
    } else {
      elimWrapper.style.display = 'block';
      evalData.eliminated.forEach(dev => {
        const row = document.createElement('tr');
        const reasonBadgeClass = dev.elimination_type === 'hard_constraint' ? 'elim-reason-badge' : 'elim-reason-badge';
        const weightText = dev.weight_kg ? `${dev.weight_kg.toFixed(2)} kg` : '-';
        const ramText = dev.ram_gb ? `${dev.ram_gb} GB` : '-';
        const priceText = formatTL(dev.price_try);

        row.innerHTML = `
          <td><strong>${escapeHtml(dev.brand)} ${escapeHtml(dev.model)}</strong></td>
          <td style="font-family:var(--font-mono);">${priceText}</td>
          <td style="font-size:12px;">CPU: ${dev.cpu_score || '-'} | GPU: ${dev.gpu_score || '-'} | RAM: ${ramText} | Ağırlık: ${weightText}</td>
          <td><span class="${reasonBadgeClass}">${escapeHtml(dev.reason)}</span></td>
          <td>
            <a href="${dev.google_link}" target="_blank" rel="noopener noreferrer" class="btn-link-google" style="padding:4px 8px; font-size:11px;">
              🔍 Ara
            </a>
          </td>
        `;
        elimTableBody.appendChild(row);
      });
    }
  }
}

function createDeviceCard(device, rank) {
  const card = document.createElement('div');
  card.className = `device-card ${rank === 1 ? 'top-rank' : ''}`;

  const isLaptop = device.category === 'laptop';
  const weightText = device.weight_kg ? `${device.weight_kg.toFixed(2)} kg` : 'Belirtilmemiş';
  const ramText = device.ram_gb ? `${device.ram_gb} GB` : '-';
  const storageText = device.storage_gb >= 1024 ? `${(device.storage_gb/1024).toFixed(0)} TB` : `${device.storage_gb} GB`;

  card.innerHTML = `
    <div class="device-card-header">
      <div class="device-rank-info">
        <div class="rank-badge ${rank === 1 ? 'gold' : ''}">#${rank}</div>
        <div class="device-names">
          <div class="category-sub">${escapeHtml(device.category)} · ${escapeHtml(device.brand)}</div>
          <h3>${escapeHtml(device.model)}</h3>
        </div>
      </div>
      <div class="device-score-block">
        <div class="score-display">
          <span class="score-number">%${device.suitability_score.toFixed(1)}</span>
        </div>
        <div class="score-label">KDS Uygunluk İndeksi</div>
        <div class="price-text">${formatTL(device.price_try)}</div>
      </div>
    </div>

    <!-- Specifications Table Grid -->
    <div class="specs-table-grid">
      <div class="spec-cell">
        <span class="label">İşlemci (CPU)</span>
        <span class="val">${escapeHtml(device.cpu_name)} (${device.cpu_score}/100)</span>
      </div>
      <div class="spec-cell">
        <span class="label">Grafik (GPU)</span>
        <span class="val">${escapeHtml(device.gpu_name)} (${device.gpu_score}/100)</span>
      </div>
      ${isLaptop ? `
      <div class="spec-cell">
        <span class="label">Bellek (RAM)</span>
        <span class="val">${ramText}</span>
      </div>
      <div class="spec-cell">
        <span class="label">Taşıma Ağırlığı</span>
        <span class="val">${weightText}</span>
      </div>
      ` : `
      <div class="spec-cell">
        <span class="label">Kamera / Kalem</span>
        <span class="val">${device.camera_or_stylus_score}/100</span>
      </div>
      `}
      <div class="spec-cell">
        <span class="label">Depolama</span>
        <span class="val">${storageText}</span>
      </div>
      <div class="spec-cell">
        <span class="label">Ekran Kalitesi</span>
        <span class="val">${device.display_score}/100</span>
      </div>
      <div class="spec-cell">
        <span class="label">Batarya Ömrü</span>
        <span class="val">${device.battery_score}/100</span>
      </div>
    </div>

    <!-- Decision Rationale -->
    <div class="rationale-box">
      <strong>KDS Karar Gerekçesi:</strong> ${escapeHtml(device.rationale)}
    </div>

    <!-- Footer Actions (Google Search Link) -->
    <div class="card-footer-actions">
      <a href="${device.google_link}" target="_blank" rel="noopener noreferrer" class="btn-link-google" title="Google üzerinde cihaz ve güncel fiyat sorgusu yap">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        ${escapeHtml(device.brand)} ${escapeHtml(device.model)} Fiyatını Google'da Ara
      </a>
    </div>
  `;

  return card;
}

// -------------------------------------------------------------
// 4. INVENTORY MANAGEMENT (SQLITE CRUD)
// -------------------------------------------------------------
function initInventoryTab() {
  const catFilterBtns = document.querySelectorAll('.inv-filter-btn');
  catFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      catFilterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.getAttribute('data-cat');
      loadInventory(cat);
    });
  });

  const searchInput = document.getElementById('inventory-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      filterInventoryTable(e.target.value.toLowerCase());
    });
  }

  // Modal setup
  const openModalBtn = document.getElementById('btn-open-add-device');
  const closeModalBtn = document.getElementById('btn-close-modal');
  const modal = document.getElementById('add-device-modal');
  const form = document.getElementById('add-device-form');

  if (openModalBtn && modal) {
    openModalBtn.addEventListener('click', () => modal.classList.add('open'));
  }
  if (closeModalBtn && modal) {
    closeModalBtn.addEventListener('click', () => modal.classList.remove('open'));
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('open');
    });
  }

  // Add Device Submit
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const newDev = {
        category: document.getElementById('new-cat').value,
        brand: document.getElementById('new-brand').value.trim(),
        model: document.getElementById('new-model').value.trim(),
        price_try: parseFloat(document.getElementById('new-price').value),
        ram_gb: document.getElementById('new-ram').value ? parseInt(document.getElementById('new-ram').value) : null,
        storage_gb: parseInt(document.getElementById('new-storage').value) || 512,
        weight_kg: document.getElementById('new-weight').value ? parseFloat(document.getElementById('new-weight').value) : null,
        cpu_name: document.getElementById('new-cpu-name').value.trim(),
        gpu_name: document.getElementById('new-gpu-name').value.trim(),
        cpu_score: document.getElementById('new-cpu-score').value ? parseInt(document.getElementById('new-cpu-score').value) : null,
        gpu_score: document.getElementById('new-gpu-score').value ? parseInt(document.getElementById('new-gpu-score').value) : null,
        battery_score: parseInt(document.getElementById('new-battery-score').value) || 75,
        display_score: parseInt(document.getElementById('new-display-score').value) || 80,
        camera_or_stylus_score: parseInt(document.getElementById('new-camera-score').value) || 75
      };

      try {
        const res = await fetch('/api/devices', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newDev)
        });
        const resData = await res.json();
        if (res.ok && resData.status === 'success') {
          alert('Cihaz SQLite veritabanına başarıyla kaydedildi!');
          form.reset();
          modal.classList.remove('open');
          loadInventory();
          fetchSystemInfo();
          runEvaluation();
        } else {
          alert('Hata: ' + (resData.message || 'Cihaz eklenemedi.'));
        }
      } catch (err) {
        alert('Sunucu iletişim hatası: ' + err.message);
      }
    });
  }
}

async function loadInventory(category = '') {
  const tbody = document.getElementById('inventory-table-body');
  if (!tbody) return;

  tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:20px;">SQLite veritabanı okunuyor...</td></tr>';

  try {
    const url = category ? `/api/devices?category=${category}` : '/api/devices';
    const res = await fetch(url);
    const data = await res.json();

    if (data.status === 'success') {
      state.devices = data.devices;
      renderInventoryTable(data.devices);
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:var(--burgundy);">Veritabanı okunamadı: ${err.message}</td></tr>`;
  }
}

function renderInventoryTable(devices) {
  const tbody = document.getElementById('inventory-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (devices.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:20px;">Veritabanında kayıtlı cihaz bulunamadı.</td></tr>';
    return;
  }

  devices.forEach(dev => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-search', `${dev.brand} ${dev.model} ${dev.category} ${dev.cpu_name}`.toLowerCase());

    const weightStr = dev.weight_kg ? `${dev.weight_kg.toFixed(2)} kg` : '-';
    const ramStr = dev.ram_gb ? `${dev.ram_gb} GB` : '-';
    const storageStr = dev.storage_gb >= 1024 ? `${(dev.storage_gb/1024).toFixed(0)} TB` : `${dev.storage_gb} GB`;

    tr.innerHTML = `
      <td style="font-family:var(--font-mono); font-weight:700;">#${dev.id}</td>
      <td><span class="constraint-tag">${escapeHtml(dev.category)}</span></td>
      <td><strong>${escapeHtml(dev.brand)}</strong></td>
      <td>${escapeHtml(dev.model)}</td>
      <td style="font-family:var(--font-mono); font-weight:700; color:var(--navy-primary);">${formatTL(dev.price_try)}</td>
      <td>${ramStr} / ${storageStr}</td>
      <td>${weightStr}</td>
      <td style="font-size:12px;">${escapeHtml(dev.cpu_name)} <span class="badge" style="background:#E2DDD4; color:#1C1917; padding:1px 4px; border-radius:2px;">${dev.cpu_score}</span></td>
      <td style="font-size:12px;">${escapeHtml(dev.gpu_name)} <span class="badge" style="background:#E2DDD4; color:#1C1917; padding:1px 4px; border-radius:2px;">${dev.gpu_score}</span></td>
      <td style="font-size:11px; font-family:var(--font-mono); color:var(--text-muted);">${escapeHtml(dev.last_synced_at || '-')}</td>
      <td>
        <button class="action-btn-del" onclick="deleteDeviceRecord(${dev.id}, '${escapeHtml(dev.brand)} ${escapeHtml(dev.model)}')">
          Sil
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterInventoryTable(query) {
  const rows = document.querySelectorAll('#inventory-table-body tr');
  rows.forEach(r => {
    const text = r.getAttribute('data-search') || '';
    r.style.display = text.includes(query) ? '' : 'none';
  });
}

async function deleteDeviceRecord(id, name) {
  if (!confirm(`'${name}' (ID: ${id}) cihazını SQLite veritabanından kalıcı olarak silmek istediğinize emin misiniz?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/devices/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      alert(data.message);
      loadInventory();
      fetchSystemInfo();
      runEvaluation();
    } else {
      alert('Hata: ' + data.message);
    }
  } catch (err) {
    alert('Silme işlemi başarısız: ' + err.message);
  }
}

// -------------------------------------------------------------
// 5. DATA IMPORT & RESET
// -------------------------------------------------------------
function initImportAndReset() {
  const btnSampleJson = document.getElementById('btn-load-sample-json');
  const importTextarea = document.getElementById('import-data-input');
  const btnExecuteImport = document.getElementById('btn-execute-import');
  const btnResetDb = document.getElementById('btn-reset-database');

  if (btnSampleJson && importTextarea) {
    btnSampleJson.addEventListener('click', () => {
      const sample = [
        {
          "category": "laptop",
          "brand": "MSI",
          "model": "Stealth 16 AI Studio",
          "price_try": "72.500,00 TL",
          "ram_gb": "32 GB",
          "storage_gb": "1 TB",
          "weight_kg": "1.99 kg",
          "cpu_name": "Intel Core Ultra 9 185H",
          "gpu_name": "NVIDIA GeForce RTX 4070",
          "battery_score": 75,
          "display_score": 94,
          "camera_or_stylus_score": 80
        },
        {
          "category": "phone",
          "brand": "Sony",
          "model": "Xperia 1 VI",
          "price_try": "54.000 TL",
          "ram_gb": 12,
          "storage_gb": 256,
          "weight_kg": "0.19 kg",
          "cpu_name": "Snapdragon 8 Gen 3",
          "gpu_name": "Adreno 750",
          "battery_score": 90,
          "display_score": 94,
          "camera_or_stylus_score": 95
        }
      ];
      importTextarea.value = JSON.stringify(sample, null, 2);
    });
  }

  if (btnExecuteImport && importTextarea) {
    btnExecuteImport.addEventListener('click', async () => {
      const text = importTextarea.value.trim();
      if (!text) {
        alert('Lütfen içe aktarılacak JSON veya CSV verisi giriniz.');
        return;
      }

      let payload = null;
      try {
        if (text.startsWith('[') || text.startsWith('{')) {
          payload = JSON.parse(text);
        } else {
          payload = { format: 'csv', data: text };
        }
      } catch (err) {
        payload = { format: 'csv', data: text };
      }

      try {
        const res = await fetch('/api/devices/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const resData = await res.json();
        if (res.ok && resData.status === 'success') {
          alert(`İçe Aktarma Tamamlandı!\n${resData.inserted_count} cihaz başarıyla SQLite veritabanına aktarıldı.`);
          importTextarea.value = '';
          loadInventory();
          fetchSystemInfo();
          runEvaluation();
        } else {
          alert('İçe aktarma hatası: ' + (resData.message || 'Geçersiz veri formatı.'));
        }
      } catch (err) {
        alert('İletişim hatası: ' + err.message);
      }
    });
  }

  // Database Reset
  if (btnResetDb) {
    btnResetDb.addEventListener('click', async () => {
      if (!confirm('SQLite veritabanını fabrika ayarlarına sıfırlamak istediğinize emin misiniz? Tüm özel eklenen cihazlar silinecek ve 27 orijinal örnek cihaz geri yüklenecektir.')) {
        return;
      }

      try {
        const res = await fetch('/api/reset', { method: 'POST' });
        const resData = await res.json();
        if (res.ok && resData.status === 'success') {
          alert(resData.message);
          loadInventory();
          fetchSystemInfo();
          runEvaluation();
        } else {
          alert('Sıfırlama hatası: ' + resData.message);
        }
      } catch (err) {
        alert('Sıfırlama başarısız: ' + err.message);
      }
    });
  }
}

// -------------------------------------------------------------
// 6. LIVE SYNC & SCHEDULER CONTROLS
// -------------------------------------------------------------
function initLiveSyncControls() {
  const btnHeaderSync = document.getElementById('btn-header-sync-now');
  const btnInvSync = document.getElementById('btn-inv-sync-now');
  const btnMethodologySync = document.getElementById('btn-methodology-sync-now');

  [btnHeaderSync, btnInvSync, btnMethodologySync].forEach(btn => {
    if (btn) {
      btn.addEventListener('click', triggerLiveSync);
    }
  });
}

async function triggerLiveSync() {
  const syncButtons = [
    document.getElementById('btn-header-sync-now'),
    document.getElementById('btn-inv-sync-now'),
    document.getElementById('btn-methodology-sync-now')
  ].filter(Boolean);

  syncButtons.forEach(btn => {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = '↻ Güncelleniyor...';
  });

  try {
    const res = await fetch('/api/sync/live', { method: 'POST' });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      const resStats = data.sync_result;
      alert(`Canlı Senkronizasyon Tamamlandı!\n• İncelenen: ${resStats.records_fetched}\n• Güncellenen Fiyat/Skor: ${resStats.records_updated}\n• Yeni Eklenen Cihaz: ${resStats.records_inserted}\n• Kaynak: ${resStats.source}`);
      fetchSystemInfo();
      fetchSyncStatusAndHistory();
      loadInventory();
      runEvaluation();
    } else {
      alert('Senkronizasyon hatası: ' + (data.message || 'Bilinmeyen hata'));
    }
  } catch (err) {
    alert('Sunucu iletişim hatası: ' + err.message);
  } finally {
    syncButtons.forEach(btn => {
      btn.disabled = false;
      btn.textContent = btn.dataset.originalText || '↻ Şimdi Canlı Güncelle';
    });
  }
}

async function fetchSyncStatusAndHistory() {
  const historyTbody = document.getElementById('sync-history-table-body');
  try {
    const res = await fetch('/api/sync/status');
    const data = await res.json();
    if (data.status === 'success') {
      const scheduleText = document.getElementById('scheduler-schedule-text');
      if (scheduleText && data.schedule) {
        scheduleText.textContent = data.schedule;
      }

      if (historyTbody && data.history) {
        historyTbody.innerHTML = '';
        if (data.history.length === 0) {
          historyTbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:12px;">Henüz senkronizasyon kaydı bulunmuyor.</td></tr>';
          return;
        }

        data.history.forEach(log => {
          const row = document.createElement('tr');
          const isSuccess = log.status === 'SUCCESS';
          const badgeBg = isSuccess ? '#DCFCE7' : (log.status === 'WARNING' ? '#FEF3C7' : '#FEE2E2');
          const badgeColor = isSuccess ? '#15803D' : (log.status === 'WARNING' ? '#B45309' : '#991B1B');

          row.innerHTML = `
            <td style="font-family:var(--font-mono); font-weight:600;">${log.synced_at}</td>
            <td style="font-size:11.5px; max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(log.source)}">
              ${escapeHtml(log.source)}
            </td>
            <td style="font-family:var(--font-mono);">${log.records_fetched}</td>
            <td style="font-family:var(--font-mono); color:#15803D; font-weight:600;">+${log.records_inserted}</td>
            <td style="font-family:var(--font-mono); color:var(--navy-primary); font-weight:600;">${log.records_updated}</td>
            <td>
              <span class="constraint-tag" style="background:${badgeBg}; color:${badgeColor}; font-weight:700;">
                ${log.status}
              </span>
            </td>
          `;
          historyTbody.appendChild(row);
        });
      }
    }
  } catch (err) {
    console.error('Sync history fetch error:', err);
  }
}

// -------------------------------------------------------------
// UTILITIES
// -------------------------------------------------------------
function formatTL(num) {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(num);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
