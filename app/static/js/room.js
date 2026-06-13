(() => {
  const roomId = document.body.dataset.roomId;
  const params = new URLSearchParams(window.location.search);
  const forceNewJoin = params.get('join') === '1' || params.get('new') === '1';

  if (forceNewJoin) {
    JT.clearRoomSession(roomId);
    JT.resetTabSessionId();
    window.history.replaceState({}, '', `/room/${roomId}`);
  }

  const sessionId = JT.getTabSessionId();
  let saved = JT.getRoomSession(roomId);
  let ws;
  let joined = Boolean(saved && saved.session_id === sessionId);
  let targetText = '';
  let latestTyped = '';
  let running = false;
  let personalShown = false;

  // Performance guards.
  // Local UI updates must stay instant, but network packets are throttled so
  // spam type/backspace does not create hundreds of WebSocket -> TCP commands.
  const INPUT_SEND_INTERVAL_MS = 75;
  let inputSendTimer = null;
  let lastSentTyped = null;
  let lastTypingRenderKey = '';
  let lastRaceRenderKey = '';

  const el = {
    joinModal: document.getElementById('joinModal'),
    waitingModal: document.getElementById('waitingModal'),
    joinName: document.getElementById('joinName'),
    joinBtn: document.getElementById('joinBtn'),
    joinMessage: document.getElementById('joinMessage'),
    waitingInfo: document.getElementById('waitingInfo'),
    waitingPlayers: document.getElementById('waitingPlayers'),
    hardStartBtn: document.getElementById('hardStartBtn'),
    leaveBtn: document.getElementById('leaveBtn'),
    stateLabel: document.getElementById('stateLabel'),
    countdownLabel: document.getElementById('countdownLabel'),
    raceLanes: document.getElementById('raceLanes'),
    gameTypeBadge: document.getElementById('gameTypeBadge'),
    targetText: document.getElementById('targetText'),
    typingInput: document.getElementById('typingInput'),
    typingHint: document.getElementById('typingHint'),
    personalResult: document.getElementById('personalResult'),
    globalResult: document.getElementById('globalResult'),
    backHomeBtn: document.getElementById('backHomeBtn')
  };

  connect();

  el.joinBtn.addEventListener('click', () => {
    const name = el.joinName.value.trim();
    if (!name) { el.joinMessage.textContent = 'Nama wajib diisi.'; return; }
    send('JOIN_ROOM', { name });
  });

  el.joinName.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') el.joinBtn.click();
  });

  el.hardStartBtn.addEventListener('click', () => send('HARD_START', {}));
  el.leaveBtn.addEventListener('click', () => {
    send('LEAVE_ROOM', {});
    JT.clearRoomSession(roomId);
    setTimeout(() => location.href = '/home', 300);
  });
  el.backHomeBtn.addEventListener('click', () => send('LEAVE_ROOM', {}));

  el.typingInput.addEventListener('input', () => {
    if (!running) {
      syncTypingInputToLatest();
      return;
    }

    // Fallback untuk mobile/IME/autofill.
    // Desktop keyboard utama diproses lewat keydown agar caret tidak bisa pindah.
    const rawValue = el.typingInput.value.slice(0, targetText.length);
    const sanitizedValue = sanitizeTypedValue(rawValue);

    applySanitizedInputValue(sanitizedValue);
  });

  el.typingInput.addEventListener('keydown', (event) => {
    handleCompetitionKeydown(event);
  }, true);
  
  el.typingInput.addEventListener('click', () => {
    keepCaretAtEnd();
  });
  
  el.typingInput.addEventListener('mouseup', () => {
    keepCaretAtEnd();
  });
  
  el.typingInput.addEventListener('select', () => {
    keepCaretAtEnd();
  });

  // If the hidden textarea loses focus, keep the game usable. This prevents the
  // "red chars stuck and cannot backspace" feeling when focus is on the visual
  // text div instead of the real textarea.
  document.addEventListener('keydown', (event) => {
    if (!running) return;

    // Kalau focus sudah di textarea typing, biarkan handler khusus textarea yang bekerja.
    if (document.activeElement === el.typingInput) return;

    const tag = String(document.activeElement?.tagName || '').toUpperCase();
    if (['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(tag)) return;

    handleCompetitionKeydown(event);
  }, true);

  el.targetText.addEventListener('mousedown', (event) => {
    event.preventDefault();
    if (running) {
      el.typingInput.focus();
      keepCaretAtEnd();
    }
  });

  el.targetText.addEventListener('click', (event) => {
    event.preventDefault();
    if (running) {
      el.typingInput.focus();
      keepCaretAtEnd();
    }
  });

  setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN && joined) {
      send('LATENCY_PING', { client_ts: Date.now() });
    }
  }, 2000);

  function connect() {
    ws = new WebSocket(JT.wsUrl(`/ws/room/${roomId}?session_id=${encodeURIComponent(sessionId)}`));
    ws.addEventListener('open', () => {
      if (joined) send('RESTORE_SESSION', {});
      else showJoinModal();
    });
    ws.addEventListener('message', (event) => handleEvent(JSON.parse(event.data)));
    ws.addEventListener('close', () => {
      running = false;
      el.stateLabel.textContent = 'Disconnected. Refresh untuk mencoba reconnect.';
      lockTyping('disconnected');
    });
  }

  function send(type, payload) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type, payload: payload || {} }));
  }

  function scheduleInputSend() {
    if (!running || !joined) return;
    if (latestTyped === targetText) {
      flushInputSend();
      return;
    }
    if (inputSendTimer) return;
    inputSendTimer = setTimeout(() => {
      inputSendTimer = null;
      flushInputSend();
    }, INPUT_SEND_INTERVAL_MS);
  }

  function flushInputSend() {
    if (!running || !joined) return;
    if (latestTyped === lastSentTyped) return;
    lastSentTyped = latestTyped;
    send('INPUT_UPDATE', { typed_text: latestTyped });
  }

  function handleEvent(event) {
    if (event.type === 'ERROR') {
      const message = event.payload?.message || 'Terjadi error.';
      el.joinMessage.textContent = message;
      if (/session|player belum terdaftar|leave/i.test(message)) {
        joined = false;
        saved = null;
        JT.clearRoomSession(roomId);
      }
      if (!joined) showJoinModal();
      return;
    }

    if (event.type === 'JOINED_ROOM' || event.type === 'RESTORED_SESSION') {
      const room = event.payload?.room;
      const viewer = getViewer(room);
      if (!viewer || viewer.session_id !== sessionId) return;
      joined = true;
      JT.saveRoomSession(roomId, { session_id: sessionId, name: viewer.name, is_creator: viewer.is_initiator });
      if (!running && viewer.typed_text && !latestTyped) {
        latestTyped = viewer.typed_text;
        el.typingInput.value = latestTyped;
      }
      hideJoinModal();
      renderRoom(room);
      return;
    }

    if (event.type === 'WAITING_UPDATE' || event.type === 'ROOM_PREPARE' || event.type === 'COUNTDOWN' || event.type === 'MATCH_START' || event.type === 'STATE_UPDATE') {
      const room = event.payload?.room;
      if (!joined && !getViewer(room)) {
        showJoinModal();
        return;
      }
      if (getViewer(room)) joined = true;
      renderRoom(room);
      return;
    }

    if (event.type === 'PERSONAL_RESULT') {
      personalShown = true;
      renderPersonal(event.payload.player);
      return;
    }
    if (event.type === 'GLOBAL_RESULT') {
      renderGlobal(event.payload.rankings || [], event.payload.reason || '-');
      if (event.payload.room) renderRoom(event.payload.room);
      return;
    }
  }

  function getViewer(room) {
    if (!room) return null;
    if (room.viewer && room.viewer.session_id === sessionId) return room.viewer;
    return (room.players || []).find(player => player.session_id === sessionId) || null;
  }

  function normalizeRoom(room) {
    if (!room) return room;
    const viewer = getViewer(room);
    const currentPlayers = Number(room.current_players || 0);
    return {
      ...room,
      viewer,
      can_hard_start: Boolean(
        room.state === 'waiting' &&
        currentPlayers >= 2 &&
        viewer &&
        viewer.connected &&
        (viewer.is_initiator || room.hard_start_unlocked_for_all)
      ),
    };
  }

  function renderRoom(room) {
    if (!room) return;
    room = normalizeRoom(room);
    const viewer = room.viewer;
    targetText = room.target_text || targetText;

    // Only restore server typed_text when not actively typing. During running,
    // the local textarea is the source of truth to avoid server echo rollback.
    if (!running && viewer && viewer.typed_text && !latestTyped) {
      latestTyped = viewer.typed_text;
      el.typingInput.value = latestTyped;
    }

    el.gameTypeBadge.textContent = `${room.game_type} | ${room.current_players}/${room.max_players}`;
    el.stateLabel.textContent = stateText(room.state);
    renderTypingText(targetText, latestTyped);
    renderRace(room.players || []);

    if (room.state === 'waiting') {
      running = false;
      lockTyping('waiting');
      showWaitingModal(room);
      el.countdownLabel.textContent = '-';
    } else if (room.state === 'prepare') {
      running = false;
      hideWaitingModal();
      hideJoinModal();
      lockTyping('locked');
      el.countdownLabel.textContent = Math.ceil(room.countdown_remaining || 0);
    } else if (room.state === 'running') {
      hideWaitingModal();
      hideJoinModal();
      el.countdownLabel.textContent = 'START';
      if (viewer && viewer.status === 'active') unlockTyping();
      else lockTyping('finished');
    } else if (room.state === 'finished') {
      hideWaitingModal();
      hideJoinModal();
      lockTyping('finished');
      el.countdownLabel.textContent = 'FINISH';
    }
  }

  function stateText(state) {
    return ({waiting:'Menunggu player', prepare:'Bersiap...', running:'Mulai!', finished:'Selesai'})[state] || state;
  }

  function showJoinModal() {
    el.waitingModal.classList.add('hidden');
    el.joinModal.classList.add('visible');
    el.joinModal.classList.remove('hidden');
    setTimeout(() => el.joinName.focus(), 50);
  }
  function hideJoinModal() { el.joinModal.classList.remove('visible'); el.joinModal.classList.add('hidden'); }
  function hideWaitingModal() { el.waitingModal.classList.add('hidden'); }

  function showWaitingModal(room) {
    hideJoinModal();
    el.waitingModal.classList.remove('hidden');
    el.waitingInfo.textContent = `Player ${room.current_players}/${room.max_players}. ${room.can_hard_start ? 'Bisa mulai sekarang.' : 'Menunggu player lain.'}`;
    el.waitingPlayers.innerHTML = (room.players || []).map(p => `<span class="player-pill">${escapeHtml(p.name)} ${p.connected ? '🟢' : '⚪'}</span>`).join('');
    if (room.can_hard_start) el.hardStartBtn.classList.remove('hidden');
    else el.hardStartBtn.classList.add('hidden');
  }

  function unlockTyping() {
    if (running && !el.typingInput.disabled) return;
    running = true;
    el.typingHint.textContent = 'typing';
    el.typingInput.disabled = false;
    syncTypingInputToLatest();

    setTimeout(() => {
      el.typingInput.focus();
      keepCaretAtEnd();
    }, 20);
  }

  function lockTyping(label) {
    running = false;
    el.typingHint.textContent = label;
    syncTypingInputToLatest();
    el.typingInput.disabled = true;
    el.typingInput.blur();
  }

  function renderRace(players) {
    const key = JSON.stringify((players || []).map(p => [p.session_id, p.name, p.status, p.connected, p.progress, p.wpm, p.cpm]));
    if (key === lastRaceRenderKey) return;
    lastRaceRenderKey = key;

    if (!players.length) {
      el.raceLanes.innerHTML = '<p class="muted">Belum ada player.</p>';
      return;
    }
    el.raceLanes.innerHTML = players.map(player => {
      const pct = Math.max(0, Math.min(100, Math.round((player.progress || 0) * 100)));
      const status = player.status === 'leave' ? 'leave' : player.status === 'timeout' ? 'timeout' : player.status === 'finished' ? 'finish' : (player.connected ? 'online' : 'reconnecting');
      return `<div class="race-lane">
        <div class="lane-name">${escapeHtml(player.name)} <span class="muted">${status}</span></div>
        <div class="track">
          <div class="track-fill" style="width:${pct}%"></div>
          <div class="rocket" style="left:${pct}%">🚀</div>
        </div>
        <div class="lane-stat">${pct}% | ${player.wpm || 0} WPM | ${player.cpm || 0} CPM</div>
      </div>`;
    }).join('');
  }

  function renderTypingText(target, typed) {
    if (!target) {
      if (lastTypingRenderKey !== '__empty__') {
        el.targetText.textContent = 'Target text akan muncul saat room siap.';
        lastTypingRenderKey = '__empty__';
      }
      return;
    }
    const key = `${target}\n${typed}`;
    if (key === lastTypingRenderKey) return;
    lastTypingRenderKey = key;

    let html = '';
    for (let i = 0; i < target.length; i++) {
      const expected = target[i];
      const actual = typed[i];
      let cls = 'char';
      if (i < typed.length) cls += actual === expected ? ' correct' : ' wrong';
      if (i === typed.length) cls += ' current';
      html += `<span class="${cls}">${escapeHtml(expected)}</span>`;
    }
    el.targetText.innerHTML = html;
  }

  function renderPersonal(player) {
    el.personalResult.classList.remove('muted');
    el.personalResult.innerHTML = `
      <strong>${escapeHtml(player.name)}</strong><br>
      Status: ${player.status}<br>
      Progress: ${Math.round((player.progress || 0) * 100)}%<br>
      WPM: ${player.wpm} | CPM: ${player.cpm}<br>
      Akurasi: ${player.accuracy_percent}%<br>
      Typo: ${player.typo_count}<br>
      Accuracy Point: ${player.accuracy_point}<br>
      Durasi: ${player.finish_duration ?? '-'} detik
    `;
  }

  function renderGlobal(rankings, reason) {
    el.globalResult.classList.remove('muted');
    el.globalResult.innerHTML = `<p>Reason: ${escapeHtml(reason)}</p>` +
      `<table><thead><tr><th>#</th><th>Nama</th><th>Status</th><th>Progress</th><th>WPM</th><th>CPM</th><th>Typo</th></tr></thead><tbody>` +
      rankings.map(p => `<tr><td>${p.rank}</td><td>${escapeHtml(p.name)}</td><td>${p.status}</td><td>${Math.round((p.progress||0)*100)}%</td><td>${p.wpm}</td><td>${p.cpm}</td><td>${p.typo_count}</td></tr>`).join('') +
      `</tbody></table><br><a class="btn btn-primary" href="/home">Back to Home</a>`;
  }

  function handleCompetitionKeydown(event) {
    if (!running) return;

    const key = String(event.key || '');

    // Shift dan CapsLock boleh, tapi tidak mengubah typed text secara langsung.
    if (key === 'Shift' || key === 'CapsLock') {
      return;
    }

    // Ctrl/Alt/Meta shortcut tidak boleh memengaruhi kompetisi.
    // Ini juga mencegah Ctrl+V, Ctrl+A, Ctrl+X, dll.
    if (event.ctrlKey || event.altKey || event.metaKey) {
      event.preventDefault();
      keepCaretAtEnd();
      return;
    }

    // Backspace adalah satu-satunya control key yang boleh mengubah input.
    // Selalu hapus dari belakang agar tidak ada bug caret di tengah.
    if (key === 'Backspace') {
      event.preventDefault();
      if (latestTyped.length > 0) {
        setTypedValue(latestTyped.slice(0, -1));
      } else {
        syncTypingInputToLatest();
      }
      return;
    }

    // Semua key non-karakter diblok:
    // Enter, Tab, Arrow, Home, End, PageUp, PageDown, Delete, Escape, F1-F12, dll.
    if (!isCompetitionCharacter(key)) {
      event.preventDefault();
      syncTypingInputToLatest();
      return;
    }

    // Karakter valid: huruf, angka, spasi, simbol, tanda baca.
    event.preventDefault();

    if (latestTyped.length >= targetText.length) {
      syncTypingInputToLatest();
      return;
    }

    setTypedValue(latestTyped + key);
  }

  function isCompetitionCharacter(key) {
    if (!key || key.length !== 1) return false;

    // Blok control character seperti newline, tab, escape char.
    const code = key.charCodeAt(0);
    if (code < 32 || code === 127) return false;

    return true;
  }

  function sanitizeTypedValue(value) {
    return String(value || '')
      .split('')
      .filter(ch => isCompetitionCharacter(ch))
      .join('')
      .slice(0, targetText.length);
  }

  function applySanitizedInputValue(nextValue) {
    nextValue = sanitizeTypedValue(nextValue);

    if (nextValue === latestTyped) {
      syncTypingInputToLatest();
      return;
    }

    // Mobile/IME normal biasanya menambah karakter di belakang.
    // Kalau meloncat banyak karakter, ambil 1 karakter pertama saja agar paste tidak langsung masuk semua.
    if (nextValue.length > latestTyped.length && nextValue.startsWith(latestTyped)) {
      const extra = nextValue.slice(latestTyped.length);
      const firstChar = extra.split('').find(ch => isCompetitionCharacter(ch));
      if (firstChar) {
        setTypedValue(latestTyped + firstChar);
        return;
      }
    }

    // Backspace mobile boleh selama hasilnya masih prefix dari input sebelumnya.
    if (nextValue.length < latestTyped.length && latestTyped.startsWith(nextValue)) {
      setTypedValue(nextValue);
      return;
    }

    // Kalau input berubah di tengah karena caret/selection/autofill, abaikan dan kembalikan.
    syncTypingInputToLatest();
  }

  function setTypedValue(value) {
    latestTyped = sanitizeTypedValue(value);
    el.typingInput.value = latestTyped;
    keepCaretAtEnd();
    renderTypingText(targetText, latestTyped);
    scheduleInputSend();
  }

  function syncTypingInputToLatest() {
    el.typingInput.value = latestTyped;
    keepCaretAtEnd();
    renderTypingText(targetText, latestTyped);
  }

  function keepCaretAtEnd() {
    if (!el.typingInput) return;

    const end = el.typingInput.value.length;

    try {
      el.typingInput.setSelectionRange(end, end);
    } catch (_) {
      // Aman diabaikan untuk browser yang tidak support selection range.
    }
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
  }
})();
