window.JT = (() => {
  function uuid() {
    if (crypto && crypto.randomUUID) return crypto.randomUUID();
    return 'tab-' + Date.now() + '-' + Math.random().toString(16).slice(2);
  }

  // window.name dipakai sebagai identitas fisik tab.
  // sessionStorage bisa ter-copy saat membuka tab baru dari tab lama,
  // sedangkan window.name membantu membedakan tab yang benar-benar berbeda.
  function getTabInstanceId() {
    if (!window.name || !window.name.startsWith('jt_window_')) {
      window.name = 'jt_window_' + uuid();
    }
    return window.name;
  }

  function getTabSessionId() {
    let id = sessionStorage.getItem('jt_tab_session_id');
    if (!id) {
      id = uuid();
      sessionStorage.setItem('jt_tab_session_id', id);
    }
    getTabInstanceId();
    return id;
  }

  function resetTabSessionId() {
    const id = uuid();
    sessionStorage.setItem('jt_tab_session_id', id);
    return id;
  }

  function roomKey(roomId) { return `jt_room_${roomId}`; }

  function saveRoomSession(roomId, data) {
    sessionStorage.setItem(roomKey(roomId), JSON.stringify({
      ...data,
      tab_instance_id: getTabInstanceId(),
    }));
  }

  function getRoomSession(roomId) {
    try {
      const data = JSON.parse(sessionStorage.getItem(roomKey(roomId)) || 'null');
      if (!data) return null;
      // Proteksi dari sessionStorage yang ter-copy ke tab baru.
      if (data.tab_instance_id && data.tab_instance_id !== getTabInstanceId()) return null;
      if (!data.tab_instance_id) return null;
      return data;
    } catch {
      return null;
    }
  }

  function clearRoomSession(roomId) { sessionStorage.removeItem(roomKey(roomId)); }

  function wsUrl(path) {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${location.host}${path}`;
  }

  function initTheme() {
    const saved = localStorage.getItem('jt_theme');
    if (saved === 'dark') document.body.classList.add('dark');
    const btn = document.getElementById('themeToggle');
    if (btn) btn.addEventListener('click', () => {
      document.body.classList.toggle('dark');
      localStorage.setItem('jt_theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    });
  }

  document.addEventListener('DOMContentLoaded', initTheme);
  return {
    getTabSessionId,
    resetTabSessionId,
    getTabInstanceId,
    saveRoomSession,
    getRoomSession,
    clearRoomSession,
    wsUrl,
  };
})();
